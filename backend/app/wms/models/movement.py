from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Movement(Base):
    __tablename__ = "movement"
    __table_args__ = {"schema": "wms"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    type = Column(String(24), nullable=False)
    whs_code_from = Column(String(8), nullable=True)
    location_id_from = Column(Integer, ForeignKey("wms.location.id"), nullable=True)
    whs_code_to = Column(String(8), nullable=True)
    location_id_to = Column(Integer, ForeignKey("wms.location.id"), nullable=True)
    item_code = Column(String(50), nullable=False)
    lot_no = Column(String(100), nullable=True)
    qty = Column(Numeric(18, 3), nullable=False)
    uom = Column(String(16), nullable=True)
    reference = Column(String(100), nullable=True)
    sap_doc_type = Column(String(24), nullable=True)
    sap_doc_entry = Column(Integer, nullable=True)
    idempotency_key = Column(String(64), nullable=True)
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    location_from = relationship("Location", foreign_keys=[location_id_from])
    location_to = relationship("Location", foreign_keys=[location_id_to])
