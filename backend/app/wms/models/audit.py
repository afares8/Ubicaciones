from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "wms_audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(DateTime, nullable=False, default=func.now())
    user_name = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)
