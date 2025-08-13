from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Warehouse(Base):
    __tablename__ = "warehouse"
    __table_args__ = {"schema": "wms"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    whs_code = Column(String(8), nullable=False, unique=True)
    name = Column(String(100), nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    locations = relationship("Location", back_populates="warehouse")
