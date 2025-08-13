from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.models import StockLocation, Location
from app.wms.schemas.stock import StockByLocationResponse, StockByItemResponse, StockSummaryResponse

router = APIRouter()

@router.get("/stock/by-location/{location_id}", response_model=List[StockByLocationResponse])
async def get_stock_by_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get all stock in a specific location"""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    stock = db.query(StockLocation).filter(
        StockLocation.location_id == location_id,
        StockLocation.qty > 0
    ).all()
    
    return stock

@router.get("/stock/by-item", response_model=StockByItemResponse)
async def get_stock_by_item(
    whs: str,
    item: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get stock locations for a specific item"""
    stock_locations = db.query(StockLocation).filter(
        StockLocation.whs_code == whs,
        StockLocation.item_code == item,
        StockLocation.qty > 0
    ).all()
    
    if not stock_locations:
        raise HTTPException(status_code=404, detail="No stock found for item")
    
    return StockByItemResponse(
        whs_code=whs,
        item_code=item,
        item_name=stock_locations[0].item_name,
        locations=stock_locations
    )

@router.get("/stock/summary", response_model=StockSummaryResponse)
async def get_stock_summary(
    whs: str,
    item: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Get stock summary for SAP reconciliation"""
    summary_query = text("""
        SELECT 
            whs_code,
            item_code,
            item_name,
            SUM(qty) as total_qty,
            uom,
            COUNT(DISTINCT location_id) as location_count
        FROM wms.stock_location
        WHERE whs_code = :whs AND item_code = :item AND qty > 0
        GROUP BY whs_code, item_code, item_name, uom
    """)
    
    result = db.execute(summary_query, {"whs": whs, "item": item}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="No stock found for item")
    
    return StockSummaryResponse(
        whs_code=result.whs_code,
        item_code=result.item_code,
        item_name=result.item_name,
        total_qty=result.total_qty,
        uom=result.uom,
        location_count=result.location_count
    )

@router.get("/stock/low-stock")
async def get_low_stock_locations(
    whs: Optional[str] = None,
    threshold_pct: float = 10.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.WAREHOUSE_MANAGER))
):
    """Get locations with low stock based on capacity"""
    low_stock_query = text("""
        SELECT 
            l.id as location_id,
            l.code as location_code,
            l.capacity_qty,
            l.capacity_uom,
            COALESCE(SUM(sl.qty), 0) as current_qty,
            (COALESCE(SUM(sl.qty), 0) / l.capacity_qty * 100) as utilization_pct
        FROM wms.location l
        LEFT JOIN wms.stock_location sl ON l.id = sl.location_id AND sl.qty > 0
        WHERE l.capacity_qty IS NOT NULL 
          AND l.is_active = 1
          AND (:whs IS NULL OR l.whs_code = :whs)
        GROUP BY l.id, l.code, l.capacity_qty, l.capacity_uom
        HAVING (COALESCE(SUM(sl.qty), 0) / l.capacity_qty * 100) < :threshold
        ORDER BY utilization_pct ASC
    """)
    
    results = db.execute(low_stock_query, {
        "whs": whs,
        "threshold": threshold_pct
    }).fetchall()
    
    return {
        "ok": True,
        "data": [
            {
                "location_id": row.location_id,
                "location_code": row.location_code,
                "capacity_qty": float(row.capacity_qty),
                "capacity_uom": row.capacity_uom,
                "current_qty": float(row.current_qty),
                "utilization_pct": float(row.utilization_pct)
            }
            for row in results
        ]
    }
