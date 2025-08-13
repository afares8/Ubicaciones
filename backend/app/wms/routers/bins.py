from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.models import Location
from app.wms.schemas.locations import LocationResponse

router = APIRouter()

@router.get("/bins/search", response_model=List[LocationResponse])
async def search_bins(
    q: str,
    whs: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Search bins by code or name"""
    query = db.query(Location).filter(Location.is_active == True)
    
    if whs:
        query = query.filter(Location.whs_code == whs)
    
    if type:
        query = query.filter(Location.type == type)
    
    query = query.filter(
        (Location.code.like(f"%{q}%")) | 
        (Location.name.like(f"%{q}%"))
    ).limit(limit)
    
    return query.all()

@router.get("/bins/{bin_id}/capacity")
async def get_bin_capacity(
    bin_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get bin capacity information"""
    location = db.query(Location).filter(Location.id == bin_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Bin not found")
    
    from sqlalchemy import text, func
    
    current_stock_query = text("""
        SELECT 
            COALESCE(SUM(qty), 0) as total_qty,
            COUNT(*) as item_count
        FROM wms.stock_location 
        WHERE location_id = :location_id AND qty > 0
    """)
    
    result = db.execute(current_stock_query, {"location_id": bin_id}).fetchone()
    
    return {
        "ok": True,
        "data": {
            "location_id": bin_id,
            "location_code": location.code,
            "capacity_qty": float(location.capacity_qty) if location.capacity_qty else None,
            "capacity_uom": location.capacity_uom,
            "current_qty": float(result.total_qty) if result else 0,
            "current_items": result.item_count if result else 0,
            "utilization_pct": (float(result.total_qty) / float(location.capacity_qty) * 100) if location.capacity_qty and result else None
        }
    }
