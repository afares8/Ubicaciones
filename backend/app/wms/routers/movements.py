from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.schemas.movements import (
    PutawayRequest, IssueRequest, MoveInternalRequest, 
    TransferWarehouseRequest, MovementResponse
)
from app.wms.services.putaway import PutawayService
from app.wms.services.transfers import TransferService

router = APIRouter()

@router.post("/operations/putaway", response_model=MovementResponse)
async def putaway_operation(
    request: PutawayRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Execute put-away operation"""
    service = PutawayService(db)
    
    lines = [
        {
            "item": line.item,
            "lot": line.lot,
            "qty": line.qty,
            "toLocationId": line.toLocationId
        }
        for line in request.lines
    ]
    
    result = await service.execute_putaway(
        whs=request.whs,
        lines=lines,
        user=current_user["username"],
        create_good_receipt=False
    )
    
    return MovementResponse(**result)

@router.post("/operations/issue", response_model=MovementResponse)
async def issue_operation(
    request: IssueRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Execute issue operation"""
    try:
        from app.wms.services.sap_client import SAPClient
        from app.wms.services.audit import WMSAuditService
        from app.wms.utils import generate_idempotency_key
        from sqlalchemy import text
        
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()
        
        with db.begin():
            movements = []
            
            for line in request.lines:
                dec_query = text("""
                    UPDATE wms.stock_location
                       SET qty = qty - :q, last_updated = SYSUTCDATETIME()
                     WHERE whs_code=:w AND location_id=:loc AND item_code=:it
                       AND (lot_no IS NULL OR lot_no=:lot) AND qty >= :q
                """)
                
                result = db.execute(dec_query, {
                    "q": float(line.qty), "w": request.whs, "loc": line.fromLocationId,
                    "it": line.item, "lot": line.lot
                })
                
                if result.rowcount == 0:
                    raise Exception(f"Insufficient stock for {line.item}")
                
                from app.wms.models import Movement
                movement = Movement(
                    type="ISSUE",
                    whs_code_from=request.whs,
                    location_id_from=line.fromLocationId,
                    item_code=line.item,
                    lot_no=line.lot,
                    qty=line.qty,
                    reference=f"ISSUE-{request.reason}-{idempotency_key}",
                    idempotency_key=idempotency_key,
                    created_by=current_user["username"]
                )
                db.add(movement)
                movements.append(movement)
            
            if request.sap and request.sap.get("createGoodIssue"):
                sap_client = SAPClient()
                sap_lines = [
                    {
                        "item": line.item,
                        "qty": float(line.qty),
                        "lot": line.lot
                    }
                    for line in request.lines
                ]
                
                sap_result = await sap_client.good_issue(
                    whs=request.whs,
                    reference=request.sap.get("reference", f"ISSUE-{idempotency_key}"),
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
                action="issue",
                payload={
                    "whs": request.whs,
                    "reason": request.reason,
                    "lines": [line.dict() for line in request.lines],
                    "sap": request.sap,
                    "idempotency_key": idempotency_key
                }
            )
            
            return MovementResponse(ok=True, data={"movements_created": len(movements)})
            
    except Exception as e:
        return MovementResponse(ok=False, error={"code": "ISSUE_FAILED", "message": str(e)})

@router.post("/operations/move-internal", response_model=MovementResponse)
async def move_internal_operation(
    request: MoveInternalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Execute internal move operation"""
    service = TransferService(db)
    
    moves = [
        {
            "item": move.item,
            "lot": move.lot,
            "qty": move.qty,
            "fromLocationId": move.fromLocationId,
            "toLocationId": move.toLocationId
        }
        for move in request.moves
    ]
    
    result = await service.execute_internal_move(
        whs=request.whs,
        moves=moves,
        user=current_user["username"]
    )
    
    return MovementResponse(**result)

@router.post("/operations/transfer-warehouse", response_model=MovementResponse)
async def transfer_warehouse_operation(
    request: TransferWarehouseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Execute cross-warehouse transfer operation"""
    service = TransferService(db)
    
    moves = [
        {
            "item": move.item,
            "lot": move.lot,
            "qty": move.qty,
            "fromLocationId": move.fromLocationId,
            "toLocationId": move.toLocationId
        }
        for move in request.moves
    ]
    
    create_sap_transfer = request.sap.get("createTransfer", True) if request.sap else True
    
    result = await service.execute_warehouse_transfer(
        from_whs=request.fromWhs,
        to_whs=request.toWhs,
        moves=moves,
        user=current_user["username"],
        create_sap_transfer=create_sap_transfer
    )
    
    return MovementResponse(**result)
