import os
import logging
import aiohttp
import base64
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.wms.models import Location
from app.wms.services.audit import WMSAuditService

logger = logging.getLogger(__name__)

class PrintingService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = WMSAuditService(db)
        self.api_key = os.getenv("PRINTNODE_API_KEY")
        self.printer_name = os.getenv("PRINTNODE_PRINTER_NAME", "WMS Label Printer")
        self.base_url = "https://api.printnode.com"

    def generate_bin_label_zpl(self, location: Location) -> str:
        """Generate ZPL for bin location label"""
        warehouse_name = location.warehouse.name or location.whs_code
        location_code = location.code
        location_name = location.name or ""
        
        attributes_text = ""
        if location.attributes:
            import json
            try:
                attrs = json.loads(location.attributes) if isinstance(location.attributes, str) else location.attributes
                attributes_text = " | ".join([f"{k}: {v}" for k, v in attrs.items()])
            except:
                attributes_text = str(location.attributes)
        
        zpl = f"""
^XA
^CF0,60
^FO50,50^FD{warehouse_name}^FS
^CF0,40
^FO50,120^FD{location_code}^FS
^CF0,30
^FO50,170^FD{location_name}^FS
^CF0,25
^FO50,210^FD{attributes_text}^FS
^BY3,3,100
^FO50,250^BC^FD{location_code}^FS
^XZ
"""
        return zpl.strip()

    def generate_bin_label_pdf(self, location: Location) -> bytes:
        """Generate PDF for bin location label"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.graphics.barcode import code128
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        warehouse_name = location.warehouse.name or location.whs_code
        location_code = location.code
        location_name = location.name or ""
        
        p.setFont("Helvetica-Bold", 24)
        p.drawString(1*inch, 9*inch, warehouse_name)
        
        p.setFont("Helvetica-Bold", 18)
        p.drawString(1*inch, 8.5*inch, location_code)
        
        p.setFont("Helvetica", 14)
        p.drawString(1*inch, 8*inch, location_name)
        
        if location.attributes:
            import json
            try:
                attrs = json.loads(location.attributes) if isinstance(location.attributes, str) else location.attributes
                attributes_text = " | ".join([f"{k}: {v}" for k, v in attrs.items()])
                p.setFont("Helvetica", 10)
                p.drawString(1*inch, 7.5*inch, attributes_text)
            except:
                pass
        
        barcode = code128.Code128(location_code, barHeight=0.5*inch, barWidth=1.5)
        barcode.drawOn(p, 1*inch, 6*inch)
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.getvalue()

    async def print_bin_label(
        self, 
        location_id: int, 
        format: str = "zpl",
        user: str = "system"
    ) -> Dict[str, Any]:
        """Print bin location label"""
        try:
            location = self.db.query(Location).filter(Location.id == location_id).first()
            if not location:
                return {"ok": False, "error": {"code": "LOCATION_NOT_FOUND", "message": "Location not found"}}
            
            if format.lower() == "zpl":
                label_content = self.generate_bin_label_zpl(location)
                content_type = "raw_base64"
                content = base64.b64encode(label_content.encode()).decode()
            elif format.lower() == "pdf":
                label_content = self.generate_bin_label_pdf(location)
                content_type = "pdf_base64"
                content = base64.b64encode(label_content).decode()
            else:
                return {"ok": False, "error": {"code": "INVALID_FORMAT", "message": "Format must be 'zpl' or 'pdf'"}}
            
            if not self.api_key:
                await self.audit_service.log_action(
                    user_name=user,
                    action="generate_label",
                    payload={
                        "location_id": location_id,
                        "location_code": location.code,
                        "format": format
                    }
                )
                return {"ok": True, "data": {"content": content, "format": format, "printed": False, "message": "Label generated but not printed (PrintNode not configured)"}}
            
            printer_id = await self._find_printer_by_name()
            if not printer_id:
                return {"ok": False, "error": {"code": "PRINTER_NOT_FOUND", "message": f"Printer '{self.printer_name}' not found"}}
            
            print_job = {
                "printerId": printer_id,
                "title": f"Bin Label - {location.code}",
                "contentType": content_type,
                "content": content,
                "source": "WMS Bin Location System"
            }
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_key, "")
                async with session.post(f"{self.base_url}/printjobs", json=print_job, auth=auth) as response:
                    if response.status == 201:
                        result = await response.json()
                        
                        await self.audit_service.log_action(
                            user_name=user,
                            action="print_label",
                            payload={
                                "location_id": location_id,
                                "location_code": location.code,
                                "format": format,
                                "print_job_id": result
                            }
                        )
                        
                        return {"ok": True, "data": {"job_id": result, "printed": True}}
                    else:
                        error_text = await response.text()
                        return {"ok": False, "error": {"code": "PRINT_FAILED", "message": error_text}}
                        
        except Exception as e:
            logger.error(f"Print label failed: {str(e)}")
            return {"ok": False, "error": {"code": "PRINT_ERROR", "message": str(e)}}

    async def _find_printer_by_name(self) -> Optional[int]:
        """Find printer ID by name"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.api_key, "")
                async with session.get(f"{self.base_url}/printers", auth=auth) as response:
                    if response.status == 200:
                        printers = await response.json()
                        for printer in printers:
                            if printer.get("name") == self.printer_name:
                                return printer.get("id")
                    return None
        except Exception as e:
            logger.error(f"Error finding printer: {str(e)}")
            return None
