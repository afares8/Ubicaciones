from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base

class Location(Base):
    __tablename__ = "location"
    __table_args__ = {"schema": "wms"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    whs_code = Column(String(8), ForeignKey("wms.warehouse.whs_code"), nullable=False)
    code = Column(String(64), nullable=False)
    name = Column(String(128), nullable=True)
    section = Column(String(32), nullable=True)
    aisle = Column(String(32), nullable=True)
    rack = Column(String(32), nullable=True)
    level = Column(String(32), nullable=True)
    bin = Column(String(32), nullable=True)
    parent_id = Column(Integer, ForeignKey("wms.location.id"), nullable=True)
    type = Column(String(16), nullable=True)
    capacity_qty = Column(Numeric(18, 3), nullable=True)
    capacity_uom = Column(String(16), nullable=True)
    attributes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    warehouse = relationship("Warehouse", back_populates="locations")
    parent = relationship("Location", remote_side=[id])
    children = relationship("Location")
    stock_locations = relationship("StockLocation", back_populates="location")

    __table_args__ = (
        {"schema": "wms"},
    )
