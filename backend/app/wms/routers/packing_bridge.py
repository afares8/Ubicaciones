from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.services.audit import WMSAuditService

router = APIRouter()

@router.get("/picking/suggestions")
async def get_picking_suggestions(
    whs: str,
    item: str,
    qty: float,
    policy: str = "FIFO",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get picking suggestions for packing operations"""
    try:
        if policy.upper() == "FIFO":
            order_clause = "sl.last_updated ASC"
        elif policy.upper() == "FEFO":
            order_clause = "sl.lot_no ASC"
        else:
            order_clause = "sl.last_updated ASC"
        
        suggestions_query = text(f"""
            SELECT 
                sl.location_id,
                l.code as location_code,
                sl.item_code,
                sl.lot_no,
                sl.qty as available_qty,
                sl.uom
            FROM wms.stock_location sl
            JOIN wms.location l ON sl.location_id = l.id
            WHERE sl.whs_code = :whs 
              AND sl.item_code = :item 
              AND sl.qty > 0
              AND l.is_active = 1
            ORDER BY {order_clause}
        """)
        
        results = db.execute(suggestions_query, {"whs": whs, "item": item}).fetchall()
        
        suggestions = []
        remaining_qty = qty
        
        for row in results:
            if remaining_qty <= 0:
                break
            
            pick_qty = min(float(row.available_qty), remaining_qty)
            
            suggestions.append({
                "locationId": row.location_id,
                "locationCode": row.location_code,
                "availableQty": float(row.available_qty),
                "suggestedQty": pick_qty,
                "lot": row.lot_no,
                "policy": policy.upper()
            })
            
            remaining_qty -= pick_qty
        
        return {
            "ok": True,
            "data": {
                "suggestions": suggestions,
                "total_available": sum(float(row.available_qty) for row in results),
                "requested_qty": qty,
                "can_fulfill": remaining_qty <= 0
            }
        }
        
    except Exception as e:
        return {"ok": False, "error": {"code": "PICKING_SUGGESTIONS_FAILED", "message": str(e)}}

@router.post("/picking/confirm")
async def confirm_picking(
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Confirm picking allocations for packing"""
    try:
        from app.wms.utils import generate_idempotency_key
        from app.wms.models import Movement
        
        reference = request.get("reference", "")
        whs = request["whs"]
        allocations = request["allocations"]
        sap_config = request.get("sap", {})
        
        idempotency_key = generate_idempotency_key()
        
        with db.begin():
            movements = []
            
            for allocation in allocations:
                item_code = allocation["item"]
                lot_no = allocation.get("lot")
                qty = float(allocation["qty"])
                from_location_id = allocation["fromLocationId"]
                
                dec_query = text("""
                    UPDATE wms.stock_location
                       SET qty = qty - :q, last_updated = SYSUTCDATETIME()
                     WHERE whs_code=:w AND location_id=:loc AND item_code=:it
                       AND (lot_no IS NULL OR lot_no=:lot) AND qty >= :q
                """)
                
                result = db.execute(dec_query, {
                    "q": qty, "w": whs, "loc": from_location_id,
                    "it": item_code, "lot": lot_no
                })
                
                if result.rowcount == 0:
                    raise Exception(f"Insufficient stock for {item_code} at location {from_location_id}")
                
                movement = Movement(
                    type="ISSUE",
                    whs_code_from=whs,
                    location_id_from=from_location_id,
                    item_code=item_code,
                    lot_no=lot_no,
                    qty=qty,
                    reference=f"PICK-{reference}",
                    idempotency_key=idempotency_key,
                    created_by=current_user["username"]
                )
                db.add(movement)
                movements.append(movement)
            
            if not sap_config.get("packingCreatesDelivery", False):
                from app.wms.services.sap_client import SAPClient
                sap_client = SAPClient()
                
                sap_lines = [
                    {
                        "item": allocation["item"],
                        "qty": float(allocation["qty"]),
                        "lot": allocation.get("lot")
                    }
                    for allocation in allocations
                ]
                
                sap_result = await sap_client.good_issue(
                    whs=whs,
                    reference=reference,
                    lines=sap_lines,
                    idempotency_key=idempotency_key
                )
                
                if not sap_result.get("ok"):
                    raise Exception(f"SAP Good Issue failed: {sap_result.get('error')}")
                
                for movement in movements:
                    movement.sap_doc_type = "GoodIssue"
                    movement.sap_doc_entry = sap_result.get("data", {}).get("docEntry")
            
            audit_service = WMSAuditService(db)
            await audit_service.log_action(
                user_name=current_user["username"],
                action="confirm_picking",
                payload={
                    "reference": reference,
                    "whs": whs,
                    "allocations": allocations,
                    "sap": sap_config,
                    "idempotency_key": idempotency_key
                }
            )
            
            return {
                "ok": True,
                "data": {
                    "movements_created": len(movements),
                    "reference": reference,
                    "sap_document_created": not sap_config.get("packingCreatesDelivery", False)
                }
            }
            
    except Exception as e:
        return {"ok": False, "error": {"code": "PICKING_CONFIRM_FAILED", "message": str(e)}}
