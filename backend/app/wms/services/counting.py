import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.wms.models import CountSession, CountDetail, StockLocation, Movement
from app.wms.services.sap_client import SAPClient
from app.wms.services.audit import WMSAuditService
from app.wms.utils import generate_idempotency_key

logger = logging.getLogger(__name__)

class CountingService:
    def __init__(self, db: Session):
        self.db = db
        self.sap_client = SAPClient()
        self.audit_service = WMSAuditService(db)

    async def create_count_session(
        self, 
        whs: str, 
        scope: Dict[str, Any], 
        user: str
    ) -> Dict[str, Any]:
        """Create new cycle count session"""
        try:
            session = CountSession(
                whs_code=whs,
                status="OPEN",
                created_by=user
            )
            self.db.add(session)
            self.db.flush()
            
            location_ids = scope.get("locations", [])
            
            for location_id in location_ids:
                stock_query = text("""
                    SELECT item_code, lot_no, qty
                    FROM wms.stock_location
                    WHERE location_id = :loc_id AND qty > 0
                """)
                
                stock_results = self.db.execute(stock_query, {"loc_id": location_id})
                
                for row in stock_results:
                    detail = CountDetail(
                        session_id=session.id,
                        location_id=location_id,
                        item_code=row.item_code,
                        lot_no=row.lot_no,
                        expected_qty=float(row.qty),
                        counted_qty=None,
                        adjusted=False
                    )
                    self.db.add(detail)
            
            self.db.commit()
            
            await self.audit_service.log_action(
                user_name=user,
                action="create_count_session",
                payload={
                    "session_id": session.id,
                    "whs": whs,
                    "scope": scope
                }
            )
            
            return {"ok": True, "data": {"session_id": session.id}}
            
        except Exception as e:
            logger.error(f"Create count session failed: {str(e)}")
            return {"ok": False, "error": {"code": "CREATE_COUNT_FAILED", "message": str(e)}}

    async def enter_counts(
        self, 
        session_id: int, 
        counts: List[Dict[str, Any]], 
        user: str
    ) -> Dict[str, Any]:
        """Enter counted quantities"""
        try:
            session = self.db.query(CountSession).filter(CountSession.id == session_id).first()
            if not session or session.status != "OPEN":
                return {"ok": False, "error": {"code": "INVALID_SESSION", "message": "Session not found or not open"}}
            
            for count in counts:
                detail_id = count["detailId"]
                counted_qty = float(count["countedQty"])
                
                detail = self.db.query(CountDetail).filter(CountDetail.id == detail_id).first()
                if detail:
                    detail.counted_qty = counted_qty
            
            self.db.commit()
            
            await self.audit_service.log_action(
                user_name=user,
                action="enter_counts",
                payload={
                    "session_id": session_id,
                    "counts": counts
                }
            )
            
            return {"ok": True, "data": {"counts_entered": len(counts)}}
            
        except Exception as e:
            logger.error(f"Enter counts failed: {str(e)}")
            return {"ok": False, "error": {"code": "ENTER_COUNTS_FAILED", "message": str(e)}}

    async def apply_count_adjustments(
        self, 
        session_id: int, 
        create_sap_adjustments: bool, 
        comment: str, 
        user: str
    ) -> Dict[str, Any]:
        """Apply count adjustments and create SAP documents if needed"""
        try:
            idempotency_key = generate_idempotency_key()
            
            with self.db.begin():
                session = self.db.query(CountSession).filter(CountSession.id == session_id).first()
                if not session or session.status != "OPEN":
                    return {"ok": False, "error": {"code": "INVALID_SESSION", "message": "Session not found or not open"}}
                
                details = self.db.query(CountDetail).filter(CountDetail.session_id == session_id).all()
                adjustments = []
                
                for detail in details:
                    if detail.counted_qty is not None:
                        diff = float(detail.counted_qty) - float(detail.expected_qty)
                        
                        if abs(diff) > 0.001:
                            update_query = text("""
                                UPDATE wms.stock_location
                                   SET qty = :new_qty, last_updated = SYSUTCDATETIME()
                                 WHERE location_id = :loc_id AND item_code = :item
                                   AND ISNULL(lot_no, '') = ISNULL(:lot, '')
                            """)
                            
                            self.db.execute(update_query, {
                                "new_qty": detail.counted_qty,
                                "loc_id": detail.location_id,
                                "item": detail.item_code,
                                "lot": detail.lot_no
                            })
                            
                            movement_type = "ADJUST_POS" if diff > 0 else "ADJUST_NEG"
                            movement = Movement(
                                type=movement_type,
                                whs_code_to=session.whs_code if diff > 0 else None,
                                whs_code_from=session.whs_code if diff < 0 else None,
                                location_id_to=detail.location_id if diff > 0 else None,
                                location_id_from=detail.location_id if diff < 0 else None,
                                item_code=detail.item_code,
                                lot_no=detail.lot_no,
                                qty=abs(diff),
                                reference=f"COUNT-{session_id}-{comment}",
                                idempotency_key=idempotency_key,
                                created_by=user
                            )
                            self.db.add(movement)
                            
                            detail.adjusted = True
                            adjustments.append({
                                "item": detail.item_code,
                                "lot": detail.lot_no,
                                "diff": diff,
                                "type": movement_type
                            })
                
                if create_sap_adjustments and adjustments:
                    positive_lines = [adj for adj in adjustments if adj["diff"] > 0]
                    negative_lines = [adj for adj in adjustments if adj["diff"] < 0]
                    
                    if positive_lines:
                        sap_lines = [
                            {
                                "item": adj["item"],
                                "qty": abs(adj["diff"]),
                                "lot": adj["lot"]
                            }
                            for adj in positive_lines
                        ]
                        
                        await self.sap_client.good_receipt(
                            whs=session.whs_code,
                            reference=f"COUNT-ADJ-{session_id}",
                            lines=sap_lines,
                            idempotency_key=f"{idempotency_key}-POS"
                        )
                    
                    if negative_lines:
                        sap_lines = [
                            {
                                "item": adj["item"],
                                "qty": abs(adj["diff"]),
                                "lot": adj["lot"]
                            }
                            for adj in negative_lines
                        ]
                        
                        await self.sap_client.good_issue(
                            whs=session.whs_code,
                            reference=f"COUNT-ADJ-{session_id}",
                            lines=sap_lines,
                            idempotency_key=f"{idempotency_key}-NEG"
                        )
                
                session.status = "CLOSED"
                session.closed_at = func.now()
                
                await self.audit_service.log_action(
                    user_name=user,
                    action="apply_count_adjustments",
                    payload={
                        "session_id": session_id,
                        "adjustments": adjustments,
                        "create_sap_adjustments": create_sap_adjustments,
                        "comment": comment,
                        "idempotency_key": idempotency_key
                    }
                )
                
                return {"ok": True, "data": {"adjustments_applied": len(adjustments)}}
                
        except Exception as e:
            logger.error(f"Apply count adjustments failed: {str(e)}")
            return {"ok": False, "error": {"code": "APPLY_ADJUSTMENTS_FAILED", "message": str(e)}}
