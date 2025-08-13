from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class CountSession(Base):
    __tablename__ = "count_session"
    __table_args__ = {"schema": "wms"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    whs_code = Column(String(8), nullable=False)
    status = Column(String(16), nullable=False, default='OPEN')
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    closed_at = Column(DateTime, nullable=True)

    details = relationship("CountDetail", back_populates="session")

class CountDetail(Base):
    __tablename__ = "count_detail"
    __table_args__ = {"schema": "wms"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("wms.count_session.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("wms.location.id"), nullable=False)
    item_code = Column(String(50), nullable=False)
    lot_no = Column(String(100), nullable=True)
    expected_qty = Column(Numeric(18, 3), nullable=False)
    counted_qty = Column(Numeric(18, 3), nullable=True)
    adjusted = Column(Boolean, nullable=False, default=False)

    session = relationship("CountSession", back_populates="details")
    location = relationship("Location")
