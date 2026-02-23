from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.config.database import Base
from src.core.enums import TransmissionType,FuelType,DriveType,VehicleType

class Make(Base):
    __tablename__ = "makes"
    id = Column(Integer,primary_key=True)
    name = Column(String(50),nullable=False,unique=True,index=True)
    is_active = Column(Boolean,default=True)
    models = relationship("Model",back_populates="make")

class Model(Base):
    __tablename__ = "models"
    id = Column(Integer,primary_key=True)
    name = Column(String(50),nullable=False,index=True)
    make_id = Column(Integer,ForeignKey("makes.id"),nullable=False)
    is_active = Column(Boolean,default=True)
    make = relationship("Make",back_populates="models")
    vehicle = relationship("Vehicle",back_populates="model")

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True,index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    year = Column(Integer,nullable=False,index=True)
    engine = Column(String(50),nullable = True)
    is_active = Column(Boolean,default=True)
    # Your Enums
    vehicle_type = Column(SQLEnum(VehicleType, native_enum=False), nullable=False)
    fuel_type    = Column(SQLEnum(FuelType, native_enum=False), nullable=False)
    drive_type   = Column(SQLEnum(DriveType, native_enum=False), nullable=False)
    transmission = Column(SQLEnum(TransmissionType, native_enum=False), nullable=False)
    # relation 
    model = relationship("Model",back_populates="vehicle")
    product_links = relationship("ProductVehicleCompatibility", back_populates="vehicle")
    # NEW: Link to ServiceVehicleCompatibility
    service_links = relationship("ServiceVehicleCompatibility", back_populates="vehicle")


