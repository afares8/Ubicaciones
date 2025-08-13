import os
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from app.wms.utils import generate_idempotency_key

logger = logging.getLogger(__name__)

class SAPClient:
    def __init__(self):
        self.base_url = os.getenv("SAP_DI_BASE_URL", "http://localhost:8001")
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.retry_delay = 1.0

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to SAP DI service with retries"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.request(method, url, json=data, headers=headers) as response:
                        result = await response.json()
                        
                        if response.status == 200:
                            return result
                        else:
                            logger.error(f"SAP DI service error: {response.status} - {result}")
                            if attempt == self.max_retries - 1:
                                return {"ok": False, "error": {"code": response.status, "message": str(result)}}
                            
            except Exception as e:
                logger.error(f"SAP DI service request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"ok": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}
                
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return {"ok": False, "error": {"code": "MAX_RETRIES_EXCEEDED", "message": "Failed after maximum retries"}}

    async def health_check(self) -> Dict[str, Any]:
        """Check SAP DI service health"""
        return await self._make_request("GET", "/health")

    async def good_receipt(
        self, 
        whs: str, 
        reference: str, 
        lines: list,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Good Receipt in SAP"""
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()
            
        data = {
            "whs": whs,
            "reference": reference,
            "lines": lines
        }
        
        return await self._make_request("POST", "/Inventory/GoodReceipt", data, idempotency_key)

    async def good_issue(
        self, 
        whs: str, 
        reference: str, 
        lines: list,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Good Issue in SAP"""
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()
            
        data = {
            "whs": whs,
            "reference": reference,
            "lines": lines
        }
        
        return await self._make_request("POST", "/Inventory/GoodIssue", data, idempotency_key)

    async def inventory_transfer(
        self, 
        from_whs: str, 
        to_whs: str, 
        reference: str, 
        lines: list,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Inventory Transfer in SAP"""
        if not idempotency_key:
            idempotency_key = generate_idempotency_key()
            
        data = {
            "fromWhs": from_whs,
            "toWhs": to_whs,
            "reference": reference,
            "lines": lines
        }
        
        return await self._make_request("POST", "/Inventory/Transfer", data, idempotency_key)
