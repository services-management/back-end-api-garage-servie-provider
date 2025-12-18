from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, Date, Text
from sqlalchemy.orm import relationship
from src.config.database import Base
from pydantic import BaseModel
from typing import Optional

class Category(Base):
    class ProductCreate(BaseModel):
        name: str
        unit_cost: Optional[float] = None
        selling_price: float
        category_id: int

    class ProductUpdate(BaseModel):
        name: Optional[str] = None
        unit_cost: Optional[float] = None
        selling_price: Optional[float] = None
        category_id: Optional[int] = None
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String,nullable=False)
    description = Column(Text, nullable=True)
    # Relationship to Product (One-to-Many)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit_cost = Column(Numeric(10,2),nullable=True)
    selling_price = Column(Numeric(10,2), nullable=False)
    # foreign key 
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    # relation
    category = relationship("Category", back_populates="products")
    # one to one relationship with inventory
    inventory = relationship("Inventory", back_populates="product", uselist=False)


class Inventory(Base):
    __tablename__ = 'inventory'

    product_id = Column(Integer, ForeignKey('products.product_id'),primary_key=True)
    current_stock = Column(Numeric(10,2), nullable=False, default=0)
    min_stock_level = Column(Numeric(10,2), nullable=True)
    last_restock_data = Column(Date, nullable=True)

    # relation
    product = relationship("Product",back_populates='inventory')