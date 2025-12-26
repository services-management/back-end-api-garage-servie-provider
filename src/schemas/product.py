from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, Date, Text
from sqlalchemy.orm import relationship
from src.config.database import Base

class Category(Base):
    __tablename__ = "categories"

    categoryID = Column(Integer, primary_key=True, index=True)
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
    category_id = Column(Integer, ForeignKey("categories.categoryID"))
    # relation
    category = relationship("Category", back_populates="products")
    # one to one relationship with inventory
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    # relationship with service associations
    service_associations = relationship("ServiceProductAssociation", back_populates="product")

class Inventory(Base):
    __tablename__ = 'inventory'

    product_id = Column(Integer, ForeignKey('products.product_id'),primary_key=True)
    current_stock = Column(Numeric(10,2), nullable=False, default=0)
    min_stock_level = Column(Numeric(10,2), nullable=True)
    last_restock_data = Column(Date, nullable=True)

    # relation
    product = relationship("Product",back_populates='inventory')


class Service(Base):
    __tablename__ = "services"
    
    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(250), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_available = Column(Boolean, server_default='True', nullable=False)
    
    associations = relationship(
        "ServiceProductAssociation",
        back_populates="service",
        cascade="all, delete-orphan"
    )


class ServiceProductAssociation(Base):
    __tablename__ = "service_products"
    
    service_id = Column(Integer, ForeignKey('services.service_id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    quantity_required = Column(Integer, nullable=False)
    is_optional = Column(Boolean, nullable=False, default=False)

    service = relationship("Service", back_populates="associations")
    product = relationship("Product", back_populates="service_associations")