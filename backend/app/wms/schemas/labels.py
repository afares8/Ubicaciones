from typing import Optional
from pydantic import BaseModel

class LabelRequest(BaseModel):
    locationId: int
    format: str = "zpl"

class LabelResponse(BaseModel):
    ok: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
