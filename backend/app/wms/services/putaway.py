import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.wms.models import StockLocation, Movement
from app.wms.services.sap_client import SAPClient
from app.wms.services.audit import WMSAuditService
from app.wms.utils import generate_idempotency_key

logger = logging.getLogger(__name__)

class PutawayService:
    def __init__(self, db: Session):
        self.db = db
        self.sap_client = SAPClient()
        self.audit_service = WMSAuditService(db)

    async def execute_putaway(
        self, 
        whs: str, 
        lines: List[Dict[str, Any]], 
        user: str,
        create_good_receipt: bool = False
    ) -> Dict[str, Any]:
        """Execute put-away operation with optional SAP Good Receipt"""
        try:
            idempotency_key = generate_idempotency_key()
            
            with self.db.begin():
                movements = []
                
                for line in lines:
                    item_code = line["item"]
                    lot_no = line.get("lot")
                    qty = float(line["qty"])
                    to_location_id = line["toLocationId"]
                    
                    stock_query = text("""
                        MERGE wms.stock_location AS t
                        USING (SELECT :whs whs_code, :loc location_id, :item item_code, :lot lot_no) s
                        ON (t.whs_code=s.whs_code AND t.location_id=s.location_id AND t.item_code=s.item_code
                            AND ISNULL(t.lot_no,'')=ISNULL(s.lot_no,''))
                        WHEN MATCHED THEN UPDATE SET qty = t.qty + :qty, last_updated = SYSUTCDATETIME()
                        WHEN NOT MATCHED THEN INSERT (whs_code, location_id, item_code, lot_no, qty)
                                             VALUES (:whs, :loc, :item, :lot, :qty);
                    """)
                    
                    self.db.execute(stock_query, {
                        "whs": whs,
                        "loc": to_location_id,
                        "item": item_code,
                        "lot": lot_no,
                        "qty": qty
                    })
                    
                    movement = Movement(
                        type="RECEIPT",
                        whs_code_to=whs,
                        location_id_to=to_location_id,
                        item_code=item_code,
                        lot_no=lot_no,
                        qty=qty,
                        reference=f"PUTAWAY-{idempotency_key}",
                        idempotency_key=idempotency_key,
                        created_by=user
                    )
                    self.db.add(movement)
                    movements.append(movement)
                
                if create_good_receipt:
                    sap_lines = [
                        {
                            "item": line["item"],
                            "qty": float(line["qty"]),
                            "lot": line.get("lot")
                        }
                        for line in lines
                    ]
                    
                    sap_result = await self.sap_client.good_receipt(
                        whs=whs,
                        reference=f"PUTAWAY-{idempotency_key}",
                        lines=sap_lines,
                        idempotency_key=idempotency_key
                    )
                    
                    if not sap_result.get("ok"):
                        raise Exception(f"SAP Good Receipt failed: {sap_result.get('error')}")
                    
                    for movement in movements:
                        movement.sap_doc_type = "GoodReceipt"
                        movement.sap_doc_entry = sap_result.get("data", {}).get("docEntry")
                
                await self.audit_service.log_action(
                    user_name=user,
                    action="putaway",
                    payload={
                        "whs": whs,
                        "lines": lines,
                        "create_good_receipt": create_good_receipt,
                        "idempotency_key": idempotency_key
                    }
                )
                
                return {"ok": True, "data": {"movements_created": len(movements)}}
                
        except Exception as e:
            logger.error(f"Putaway operation failed: {str(e)}")
            return {"ok": False, "error": {"code": "PUTAWAY_FAILED", "message": str(e)}}
