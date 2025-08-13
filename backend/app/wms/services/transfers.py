import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.wms.models import StockLocation, Movement
from app.wms.services.sap_client import SAPClient
from app.wms.services.audit import WMSAuditService
from app.wms.utils import generate_idempotency_key

logger = logging.getLogger(__name__)

class TransferService:
    def __init__(self, db: Session):
        self.db = db
        self.sap_client = SAPClient()
        self.audit_service = WMSAuditService(db)

    async def execute_internal_move(
        self, 
        whs: str, 
        moves: List[Dict[str, Any]], 
        user: str
    ) -> Dict[str, Any]:
        """Execute internal move within same warehouse (no SAP document)"""
        try:
            idempotency_key = generate_idempotency_key()
            
            with self.db.begin():
                movements = []
                
                for move in moves:
                    item_code = move["item"]
                    lot_no = move.get("lot")
                    qty = float(move["qty"])
                    from_location_id = move["fromLocationId"]
                    to_location_id = move["toLocationId"]
                    
                    dec_query = text("""
                        UPDATE wms.stock_location
                           SET qty = qty - :q, last_updated = SYSUTCDATETIME()
                         WHERE whs_code=:w AND location_id=:loc AND item_code=:it
                           AND (lot_no IS NULL OR lot_no=:lot) AND qty >= :q
                    """)
                    
                    result = self.db.execute(dec_query, {
                        "q": qty, "w": whs, "loc": from_location_id, 
                        "it": item_code, "lot": lot_no
                    })
                    
                    if result.rowcount == 0:
                        raise Exception(f"Insufficient stock or concurrent change for {item_code}")
                    
                    inc_query = text("""
                        MERGE wms.stock_location AS t
                        USING (SELECT :w whs_code, :loc location_id, :it item_code, :lot lot_no) s
                        ON (t.whs_code=s.whs_code AND t.location_id=s.location_id AND t.item_code=s.item_code
                            AND ISNULL(t.lot_no,'')=ISNULL(s.lot_no,''))
                        WHEN MATCHED THEN UPDATE SET qty = t.qty + :q, last_updated = SYSUTCDATETIME()
                        WHEN NOT MATCHED THEN INSERT (whs_code, location_id, item_code, lot_no, qty)
                                             VALUES (:w, :loc, :it, :lot, :q);
                    """)
                    
                    self.db.execute(inc_query, {
                        "q": qty, "w": whs, "loc": to_location_id,
                        "it": item_code, "lot": lot_no
                    })
                    
                    movement = Movement(
                        type="MOVE_INTERNAL",
                        whs_code_from=whs,
                        location_id_from=from_location_id,
                        whs_code_to=whs,
                        location_id_to=to_location_id,
                        item_code=item_code,
                        lot_no=lot_no,
                        qty=qty,
                        reference=f"INTERNAL-{idempotency_key}",
                        idempotency_key=idempotency_key,
                        created_by=user
                    )
                    self.db.add(movement)
                    movements.append(movement)
                
                await self.audit_service.log_action(
                    user_name=user,
                    action="internal_move",
                    payload={
                        "whs": whs,
                        "moves": moves,
                        "idempotency_key": idempotency_key
                    }
                )
                
                return {"ok": True, "data": {"movements_created": len(movements)}}
                
        except Exception as e:
            logger.error(f"Internal move failed: {str(e)}")
            return {"ok": False, "error": {"code": "INTERNAL_MOVE_FAILED", "message": str(e)}}

    async def execute_warehouse_transfer(
        self, 
        from_whs: str, 
        to_whs: str, 
        moves: List[Dict[str, Any]], 
        user: str,
        create_sap_transfer: bool = True
    ) -> Dict[str, Any]:
        """Execute cross-warehouse transfer with SAP Inventory Transfer"""
        try:
            idempotency_key = generate_idempotency_key()
            
            with self.db.begin():
                movements = []
                
                for move in moves:
                    item_code = move["item"]
                    lot_no = move.get("lot")
                    qty = float(move["qty"])
                    from_location_id = move["fromLocationId"]
                    to_location_id = move["toLocationId"]
                    
                    dec_query = text("""
                        UPDATE wms.stock_location
                           SET qty = qty - :q, last_updated = SYSUTCDATETIME()
                         WHERE whs_code=:w AND location_id=:loc AND item_code=:it
                           AND (lot_no IS NULL OR lot_no=:lot) AND qty >= :q
                    """)
                    
                    result = self.db.execute(dec_query, {
                        "q": qty, "w": from_whs, "loc": from_location_id,
                        "it": item_code, "lot": lot_no
                    })
                    
                    if result.rowcount == 0:
                        raise Exception(f"Insufficient stock or concurrent change for {item_code}")
                    
                    inc_query = text("""
                        MERGE wms.stock_location AS t
                        USING (SELECT :w whs_code, :loc location_id, :it item_code, :lot lot_no) s
                        ON (t.whs_code=s.whs_code AND t.location_id=s.location_id AND t.item_code=s.item_code
                            AND ISNULL(t.lot_no,'')=ISNULL(s.lot_no,''))
                        WHEN MATCHED THEN UPDATE SET qty = t.qty + :q, last_updated = SYSUTCDATETIME()
                        WHEN NOT MATCHED THEN INSERT (whs_code, location_id, item_code, lot_no, qty)
                                             VALUES (:w, :loc, :it, :lot, :q);
                    """)
                    
                    self.db.execute(inc_query, {
                        "q": qty, "w": to_whs, "loc": to_location_id,
                        "it": item_code, "lot": lot_no
                    })
                    
                    movement = Movement(
                        type="TRANSFER_WAREHOUSE",
                        whs_code_from=from_whs,
                        location_id_from=from_location_id,
                        whs_code_to=to_whs,
                        location_id_to=to_location_id,
                        item_code=item_code,
                        lot_no=lot_no,
                        qty=qty,
                        reference=f"TRANSFER-{idempotency_key}",
                        idempotency_key=idempotency_key,
                        created_by=user
                    )
                    self.db.add(movement)
                    movements.append(movement)
                
                if create_sap_transfer:
                    sap_lines = [
                        {
                            "item": move["item"],
                            "qty": float(move["qty"]),
                            "lot": move.get("lot")
                        }
                        for move in moves
                    ]
                    
                    sap_result = await self.sap_client.inventory_transfer(
                        from_whs=from_whs,
                        to_whs=to_whs,
                        reference=f"TRANSFER-{idempotency_key}",
                        lines=sap_lines,
                        idempotency_key=idempotency_key
                    )
                    
                    if not sap_result.get("ok"):
                        raise Exception(f"SAP Inventory Transfer failed: {sap_result.get('error')}")
                    
                    for movement in movements:
                        movement.sap_doc_type = "InventoryTransfer"
                        movement.sap_doc_entry = sap_result.get("data", {}).get("docEntry")
                
                await self.audit_service.log_action(
                    user_name=user,
                    action="warehouse_transfer",
                    payload={
                        "from_whs": from_whs,
                        "to_whs": to_whs,
                        "moves": moves,
                        "create_sap_transfer": create_sap_transfer,
                        "idempotency_key": idempotency_key
                    }
                )
                
                return {"ok": True, "data": {"movements_created": len(movements)}}
                
        except Exception as e:
            logger.error(f"Warehouse transfer failed: {str(e)}")
            return {"ok": False, "error": {"code": "WAREHOUSE_TRANSFER_FAILED", "message": str(e)}}
