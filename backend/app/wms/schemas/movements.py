from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal

class MovementLineBase(BaseModel):
    item: str
    lot: Optional[str] = None
    qty: Decimal
    fromLocationId: Optional[int] = None
    toLocationId: Optional[int] = None

class PutawayLine(BaseModel):
    item: str
    lot: Optional[str] = None
    qty: Decimal
    toLocationId: int

class PutawayRequest(BaseModel):
    whs: str
    lines: List[PutawayLine]

class IssueLine(BaseModel):
    item: str
    lot: Optional[str] = None
    qty: Decimal
    fromLocationId: int

class IssueRequest(BaseModel):
    whs: str
    reason: str
    lines: List[IssueLine]
    sap: Optional[dict] = None

class MoveInternalLine(BaseModel):
    item: str
    lot: Optional[str] = None
    qty: Decimal
    fromLocationId: int
    toLocationId: int

class MoveInternalRequest(BaseModel):
    whs: str
    moves: List[MoveInternalLine]

class TransferWarehouseLine(BaseModel):
    item: str
    lot: Optional[str] = None
    qty: Decimal
    fromLocationId: int
    toLocationId: int

class TransferWarehouseRequest(BaseModel):
    fromWhs: str
    toWhs: str
    moves: List[TransferWarehouseLine]
    sap: Optional[dict] = None

class MovementResponse(BaseModel):
    ok: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
