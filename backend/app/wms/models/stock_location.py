from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class StockLocation(Base):
    __tablename__ = "stock_location"
    __table_args__ = {"schema": "wms"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    whs_code = Column(String(8), nullable=False)
    location_id = Column(Integer, ForeignKey("wms.location.id"), nullable=False)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(200), nullable=True)
    lot_no = Column(String(100), nullable=True)
    qty = Column(Numeric(18, 3), nullable=False, default=0)
    uom = Column(String(16), nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.now())

    location = relationship("Location", back_populates="stock_locations")
