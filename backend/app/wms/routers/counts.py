from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.models import CountSession, CountDetail
from app.wms.schemas.counts import (
    CountSessionCreate, CountSessionResponse, CountDetailUpdate,
    CountApplyRequest, CountResponse
)
from app.wms.services.counting import CountingService

router = APIRouter()

@router.post("/counts", response_model=CountResponse)
async def create_count_session(
    request: CountSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER))
):
    """Create new cycle count session"""
    service = CountingService(db)
    
    result = await service.create_count_session(
        whs=request.whs,
        scope=request.scope,
        user=current_user["username"]
    )
    
    return CountResponse(**result)

@router.get("/counts/{count_id}", response_model=CountSessionResponse)
async def get_count_session(
    count_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get count session details"""
    session = db.query(CountSession).filter(CountSession.id == count_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Count session not found")
    
    return session

@router.get("/counts/{count_id}/details")
async def get_count_details(
    count_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get count session details with items"""
    session = db.query(CountSession).filter(CountSession.id == count_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Count session not found")
    
    details = db.query(CountDetail).filter(CountDetail.session_id == count_id).all()
    
    return {
        "ok": True,
        "data": {
            "session": {
                "id": session.id,
                "whs_code": session.whs_code,
                "status": session.status,
                "created_by": session.created_by,
                "created_at": session.created_at.isoformat(),
                "closed_at": session.closed_at.isoformat() if session.closed_at else None
            },
            "details": [
                {
                    "id": detail.id,
                    "location_id": detail.location_id,
                    "item_code": detail.item_code,
                    "lot_no": detail.lot_no,
                    "expected_qty": float(detail.expected_qty),
                    "counted_qty": float(detail.counted_qty) if detail.counted_qty is not None else None,
                    "adjusted": detail.adjusted
                }
                for detail in details
            ]
        }
    }

@router.put("/counts/{count_id}/enter", response_model=CountResponse)
async def enter_counts(
    count_id: int,
    counts: List[CountDetailUpdate],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Enter counted quantities"""
    service = CountingService(db)
    
    count_data = [
        {
            "detailId": count.detailId,
            "countedQty": count.countedQty
        }
        for count in counts
    ]
    
    result = await service.enter_counts(
        session_id=count_id,
        counts=count_data,
        user=current_user["username"]
    )
    
    return CountResponse(**result)

@router.post("/counts/{count_id}/apply", response_model=CountResponse)
async def apply_count_adjustments(
    count_id: int,
    request: CountApplyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER))
):
    """Apply count adjustments and create SAP documents"""
    service = CountingService(db)
    
    result = await service.apply_count_adjustments(
        session_id=count_id,
        create_sap_adjustments=request.createSapAdjustments,
        comment=request.comment or "Cycle count adjustment",
        user=current_user["username"]
    )
    
    return CountResponse(**result)

@router.get("/counts")
async def list_count_sessions(
    whs: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """List count sessions with filters"""
    query = db.query(CountSession)
    
    if whs:
        query = query.filter(CountSession.whs_code == whs)
    
    if status:
        query = query.filter(CountSession.status == status)
    
    sessions = query.order_by(CountSession.created_at.desc()).limit(limit).all()
    
    return {
        "ok": True,
        "data": [
            {
                "id": session.id,
                "whs_code": session.whs_code,
                "status": session.status,
                "created_by": session.created_by,
                "created_at": session.created_at.isoformat(),
                "closed_at": session.closed_at.isoformat() if session.closed_at else None
            }
            for session in sessions
        ]
    }
