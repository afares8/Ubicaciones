from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class CountSessionCreate(BaseModel):
    whs: str
    scope: dict

class CountSessionResponse(BaseModel):
    id: int
    whs_code: str
    status: str
    created_by: str
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CountDetailUpdate(BaseModel):
    detailId: int
    countedQty: Decimal

class CountApplyRequest(BaseModel):
    createSapAdjustments: bool = True
    comment: Optional[str] = None

class CountResponse(BaseModel):
    ok: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
