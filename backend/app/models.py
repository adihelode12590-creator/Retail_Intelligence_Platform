from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=True)  # eBay item ID, null for demo/csv data
    source = Column(String, default="csv")  # "csv" or "ebay"
    title = Column(String, nullable=False)
    description = Column(String, default="")
    category = Column(String, default="")
    price = Column(Float, default=0.0)
    brand = Column(String, default="")
    url = Column(String, nullable=True)  # link to live listing (ebay only)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
