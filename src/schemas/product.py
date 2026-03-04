import enum

from sqlalchemy import Boolean, Column, Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from src.config.database import Base
from src.core.enums import ServiceType


class ProductStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"
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
    price_adjustment = Column(Numeric(10,2), nullable=False, default=0) # Extra fee per unit for Home Service
    description = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.ACTIVE)
    # foreign key 
    category_id = Column(Integer, ForeignKey("categories.categoryID"))
    # relation
    category = relationship("Category", back_populates="products")
    # one to one relationship with inventory
    inventory = relationship("Inventory", back_populates="product", uselist=False,cascade="all, delete-orphan")
    # relationship with service associations
    service_associations = relationship("ServiceProductAssociation", back_populates="product")

    vehicle_links = relationship("ProductVehicleCompatibility", back_populates="product")
class Inventory(Base):
    __tablename__ = 'inventory'

    product_id = Column(Integer, ForeignKey('products.product_id'),primary_key=True)
    current_stock = Column(Numeric(10,2), nullable=False, default=0)
    min_stock_level = Column(Numeric(10,2), nullable=True)
    last_restock_date = Column(Date, nullable=True)
    # relation
    product = relationship("Product",back_populates='inventory')


class Service(Base):
    __tablename__ = "services"
    
    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(250), nullable=False)
    garage_price = Column(Numeric(10, 2), nullable=False, default=0)
    home_price = Column(Numeric(10, 2), nullable=False, default=0)
    duration_minutes = Column(Integer, nullable=False)
    is_available = Column(Boolean, server_default='True', nullable=False)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.ACTIVE)
    service_type = Column(SQLEnum(ServiceType, native_enum=False), nullable=False, default=ServiceType.GARAGE)
    
    associations = relationship(
        "ServiceProductAssociation",
        back_populates="service",
        cascade="all, delete-orphan"
    )
    # Add relationship to ServiceVehicleCompatibility
    vehicle_links = relationship("ServiceVehicleCompatibility", back_populates="service")


class ServiceProductAssociation(Base):
    __tablename__ = "service_products"
    
    service_id = Column(Integer, ForeignKey('services.service_id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    quantity_required = Column(Integer, nullable=False)
    is_optional = Column(Boolean, nullable=False, default=False)

    service = relationship("Service", back_populates="associations")
    product = relationship("Product", back_populates="service_associations")

class ProductVehicleCompatibility(Base):
    __tablename__ = "product_vehicle_compatibility"

    product_id = Column(Integer, ForeignKey('products.product_id'), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), primary_key=True)
    
    quantity_required = Column(String(50), nullable=True) 
    note = Column(String(255), nullable=True)
    # Relationships
    product = relationship("Product", back_populates="vehicle_links")
    vehicle = relationship("Vehicle", back_populates="product_links")

# NEW: ServiceVehicleCompatibility association table
class ServiceVehicleCompatibility(Base):
    __tablename__ = "service_vehicle_compatibility"

    service_id = Column(Integer, ForeignKey('services.service_id'), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), primary_key=True)

    note = Column(String(255), nullable=True) # Optional note for compatibility

    # Relationships
    service = relationship("Service", back_populates="vehicle_links")
    vehicle = relationship("Vehicle", back_populates="service_links") # Assuming Vehicle model will have service_links