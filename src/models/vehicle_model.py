from pydantic import BaseModel, ConfigDict
from typing import Optional
from src.core.enums import VehicleType, TransmissionType,FuelType,DriveType
# --- Base Schemas (Common Fields) ---
class MakeBase(BaseModel):
    id:int
    name: str # "Toyota"
    is_active : bool 
    model_config = ConfigDict(from_attributes=True)

class Makecreate(BaseModel):
    name:str

class Modelcreate(BaseModel):
    name:str
    make:Makecreate
class ModelBase(BaseModel):
    id:int
    name: str
    make: MakeBase
    is_active : bool 
    model_config = ConfigDict(from_attributes=True)

class Modelupdate(BaseModel):
    name:str
    
class Makeupdate(BaseModel):
    name:str
    

class VehicleBase(BaseModel):
    vehicle_id:int
    model_id: int
    year: int
    engine: Optional[str] = None
    img_url: Optional[str] = None
    vehicle_type: VehicleType
    fuel_type: FuelType
    drive_type: DriveType
    transmission: TransmissionType
    is_active : bool 
    model: ModelBase
    model_config = ConfigDict(from_attributes=True)

class VehicleCreate(BaseModel):
    """Fields required to create a new vehicle config."""
    model_id: int
    year: int
    engine: Optional[str] = None
    img_url: Optional[str] = None
    vehicle_type: VehicleType
    fuel_type: FuelType
    drive_type: DriveType
    transmission: TransmissionType
    # is_active usually defaults to True in DB, so we don't force it here

class VehicleUpdate(BaseModel):
    """All fields optional for partial updates (PATCH)."""
    model_id: Optional[int] = None
    year: Optional[int] = None
    engine: Optional[str] = None
    img_url: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    fuel_type: Optional[FuelType] = None
    drive_type: Optional[DriveType] = None
    transmission: Optional[TransmissionType] = None
    is_active: Optional[bool] = None