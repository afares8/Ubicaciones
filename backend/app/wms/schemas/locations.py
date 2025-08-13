from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from decimal import Decimal

class LocationBase(BaseModel):
    whs_code: str
    code: str
    name: Optional[str] = None
    section: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    bin: Optional[str] = None
    parent_id: Optional[int] = None
    type: Optional[str] = None
    capacity_qty: Optional[Decimal] = None
    capacity_uom: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: bool = True

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    capacity_qty: Optional[Decimal] = None
    capacity_uom: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class LocationResponse(LocationBase):
    id: int

    class Config:
        from_attributes = True

class BulkGenerateRequest(BaseModel):
    pattern: str
    type: Optional[str] = "Storage"
    attributes: Optional[Dict[str, Any]] = None

class BulkGenerateResponse(BaseModel):
    ok: bool
    data: Optional[Dict[str, int]] = None
    error: Optional[Dict[str, str]] = None
