from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.wms.deps import require_role, UserRole
from app.wms.schemas.labels import LabelRequest, LabelResponse
from app.wms.services.printing import PrintingService

router = APIRouter()

@router.post("/locations/{location_id}/label", response_model=LabelResponse)
async def generate_location_label(
    location_id: int,
    request: LabelRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Generate and optionally print location label"""
    service = PrintingService(db)
    
    result = await service.print_bin_label(
        location_id=location_id,
        format=request.format,
        user=current_user["username"]
    )
    
    return LabelResponse(**result)

@router.get("/labels/preview/{location_id}")
async def preview_location_label(
    location_id: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """Preview location label without printing"""
    from app.wms.models import Location
    
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    service = PrintingService(db)
    
    if format.lower() == "zpl":
        content = service.generate_bin_label_zpl(location)
        return {"ok": True, "data": {"content": content, "format": "zpl"}}
    elif format.lower() == "pdf":
        import base64
        content = service.generate_bin_label_pdf(location)
        content_b64 = base64.b64encode(content).decode()
        return {"ok": True, "data": {"content": content_b64, "format": "pdf"}}
    else:
        raise HTTPException(status_code=400, detail="Format must be 'zpl' or 'pdf'")

@router.get("/labels/printers")
async def list_printers(
    current_user: dict = Depends(require_role(UserRole.OPERATOR))
):
    """List available printers"""
    import os
    import aiohttp
    
    api_key = os.getenv("PRINTNODE_API_KEY")
    if not api_key:
        return {"ok": False, "error": {"code": "PRINTNODE_NOT_CONFIGURED", "message": "PrintNode API key not configured"}}
    
    try:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(api_key, "")
            async with session.get("https://api.printnode.com/printers", auth=auth) as response:
                if response.status == 200:
                    printers = await response.json()
                    return {"ok": True, "data": {"printers": printers}}
                else:
                    error_text = await response.text()
                    return {"ok": False, "error": {"code": "PRINTNODE_ERROR", "message": error_text}}
    except Exception as e:
        return {"ok": False, "error": {"code": "PRINTNODE_CONNECTION_ERROR", "message": str(e)}}
