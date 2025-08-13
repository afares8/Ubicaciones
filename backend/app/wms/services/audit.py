import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.wms.models import AuditLog
from app.wms.utils import hash_payload
from datetime import datetime

logger = logging.getLogger(__name__)

class WMSAuditService:
    def __init__(self, db: Session):
        self.db = db

    async def log_action(
        self,
        user_name: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log WMS action to audit trail"""
        try:
            audit_log = AuditLog(
                user_name=user_name,
                action=action,
                payload=json.dumps(payload) if payload else None
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            return False

    def get_audit_trail(
        self, 
        user_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Get audit trail with optional filters"""
        try:
            query = self.db.query(AuditLog)
            
            if user_name:
                query = query.filter(AuditLog.user_name == user_name)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            query = query.order_by(AuditLog.ts.desc()).limit(limit)
            
            records = []
            for log in query.all():
                record = {
                    'id': log.id,
                    'timestamp': log.ts.isoformat(),
                    'user_name': log.user_name,
                    'action': log.action,
                    'payload': json.loads(log.payload) if log.payload else None
                }
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {str(e)}")
            return []
