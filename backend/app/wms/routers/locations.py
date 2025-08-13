from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.models import Warehouse, Location
from app.wms.schemas.locations import (
    LocationCreate, LocationUpdate, LocationResponse, 
    BulkGenerateRequest, BulkGenerateResponse
)
from app.wms.utils import generate_bin_codes, validate_warehouse_code
from app.wms.services.audit import WMSAuditService

router = APIRouter()

@router.post("/warehouses/{whs}/locations/bulk-generate", response_model=BulkGenerateResponse)
async def bulk_generate_locations(
    whs: str,
    request: BulkGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER)),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Bulk generate locations from pattern"""
    try:
        if not validate_warehouse_code(whs):
            raise HTTPException(status_code=400, detail="Invalid warehouse code")
        
        warehouse = db.query(Warehouse).filter(Warehouse.whs_code == whs).first()
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        bin_codes = generate_bin_codes(request.pattern)
        created_count = 0
        
        for code in bin_codes:
            existing = db.query(Location).filter(
                Location.whs_code == whs,
                Location.code == code
            ).first()
            
            if not existing:
                parts = code.split('-')
                location = Location(
                    whs_code=whs,
                    code=code,
                    section=parts[0] if len(parts) > 0 else None,
                    aisle=parts[1] if len(parts) > 1 else None,
                    rack=parts[2] if len(parts) > 2 else None,
                    level=parts[3] if len(parts) > 3 else None,
                    bin=parts[4] if len(parts) > 4 else None,
                    type=request.type,
                    attributes=request.attributes
                )
                db.add(location)
                created_count += 1
        
        db.commit()
        
        audit_service = WMSAuditService(db)
        await audit_service.log_action(
            user_name=current_user["username"],
            action="bulk_generate_locations",
            payload={
                "warehouse": whs,
                "pattern": request.pattern,
                "created_count": created_count,
                "idempotency_key": idempotency_key
            }
        )
        
        return BulkGenerateResponse(ok=True, data={"created": created_count})
        
    except Exception as e:
        return BulkGenerateResponse(ok=False, error={"code": "BULK_GENERATE_FAILED", "message": str(e)})

@router.get("/warehouses/{whs}/locations", response_model=List[LocationResponse])
async def get_locations(
    whs: str,
    code_like: Optional[str] = None,
    type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get locations with optional filters"""
    query = db.query(Location).filter(Location.whs_code == whs)
    
    if code_like:
        query = query.filter(Location.code.like(f"%{code_like}%"))
    
    if type:
        query = query.filter(Location.type == type)
    
    if active_only:
        query = query.filter(Location.is_active == True)
    
    return query.all()

@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get specific location"""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    request: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER))
):
    """Update location"""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    
    audit_service = WMSAuditService(db)
    await audit_service.log_action(
        user_name=current_user["username"],
        action="update_location",
        payload={
            "location_id": location_id,
            "updates": update_data
        }
    )
    
    return location
