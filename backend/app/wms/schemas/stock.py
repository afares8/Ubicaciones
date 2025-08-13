from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class StockLocationBase(BaseModel):
    whs_code: str
    location_id: int
    item_code: str
    item_name: Optional[str] = None
    lot_no: Optional[str] = None
    qty: Decimal
    uom: Optional[str] = None

class StockByLocationResponse(StockLocationBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

class StockByItemResponse(BaseModel):
    whs_code: str
    item_code: str
    item_name: Optional[str] = None
    locations: List[StockByLocationResponse]

class StockSummaryResponse(BaseModel):
    whs_code: str
    item_code: str
    item_name: Optional[str] = None
    total_qty: Decimal
    uom: Optional[str] = None
    location_count: int
