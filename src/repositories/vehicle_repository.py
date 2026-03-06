# src/repositories/vehicle_repository.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.schemas.vehicle import Make, Model, Vehicle
from src.core.enums import VehicleType, TransmissionType, FuelType, DriveType

class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    # ==================== MAKE CRUD ====================

    def create_make(self, name: str) -> Make:
        db_make = Make(name=name, is_active=True)
        self.db.add(db_make)
        self.db.commit()
        self.db.refresh(db_make)
        return db_make

    def get_make_by_id(self, make_id: int) -> Optional[Make]:
        return self.db.query(Make).filter(Make.id == make_id).first()

    def get_make_by_name(self, name: str) -> Optional[Make]:
        return self.db.query(Make).filter(Make.name.ilike(name)).first()

    def get_all_makes(self, active_only: bool = True) -> List[Make]:
        query = self.db.query(Make)
        if active_only:
            query = query.filter(Make.is_active)
        return query.all()

    def update_make(self, make_id: int, name: str) -> Optional[Make]:
        db_make = self.get_make_by_id(make_id)
        if db_make:
            db_make.name = name
            self.db.commit()
            self.db.refresh(db_make)
        return db_make

    def soft_delete_make(self, make_id: int) -> bool:
        db_make = self.get_make_by_id(make_id)
        if db_make:
            db_make.is_active = False
            self.db.commit()
            return True
        return False

    # ==================== MODEL CRUD ====================

    def create_model(self, make_id: int, name: str) -> Model:
        db_model = Model(make_id=make_id, name=name, is_active=True)
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return db_model

    def get_model_by_id(self, model_id: int) -> Optional[Model]:
        return self.db.query(Model).filter(Model.id == model_id).first()

    def get_models_by_make(self, make_id: int, active_only: bool = True) -> List[Model]:
        query = self.db.query(Model).filter(Model.make_id == make_id)
        if active_only:
            query = query.filter(Model.is_active)
        return query.all()

    def update_model(self, model_id: int, name: str) -> Optional[Model]:
        db_model = self.get_model_by_id(model_id)
        if db_model:
            db_model.name = name
            self.db.commit()
            self.db.refresh(db_model)
        return db_model

    def soft_delete_model(self, model_id: int) -> bool:
        db_model = self.get_model_by_id(model_id)
        if db_model:
            db_model.is_active = False
            self.db.commit()
            return True
        return False

    # ==================== VEHICLE (CONFIG) CRUD ====================

    def create_vehicle(self, model_id: int, year: int, engine: str, 
                       v_type: VehicleType, f_type: FuelType, 
                       d_type: DriveType, trans: TransmissionType,
                       img_url: Optional[str] = None) -> Vehicle:
        db_vehicle = Vehicle(
            model_id=model_id,
            year=year,
            engine=engine,
            vehicle_type=v_type,
            fuel_type=f_type,
            drive_type=d_type,
            transmission=trans,
            img_url=img_url,
            is_active=True
        )
        self.db.add(db_vehicle)
        self.db.commit()
        self.db.refresh(db_vehicle)
        return db_vehicle

    def search_vehicles(self, 
                        model_id: Optional[int] = None, 
                        year: Optional[int] = None, 
                        engine: Optional[str] = None, 
                        vehicle_type: Optional[VehicleType] = None, 
                        fuel_type: Optional[FuelType] = None, 
                        drive_type: Optional[DriveType] = None, 
                        transmission: Optional[TransmissionType] = None) -> List[Vehicle]:
        query = self.db.query(Vehicle).filter(Vehicle.is_active)
        
        if model_id is not None:
            query = query.filter(Vehicle.model_id == model_id)
        if year is not None:
            query = query.filter(Vehicle.year == year)
        if engine is not None:
            query = query.filter(Vehicle.engine.ilike(f"%{engine}%"))
        if vehicle_type is not None:
            query = query.filter(Vehicle.vehicle_type == vehicle_type)
        if fuel_type is not None:
            query = query.filter(Vehicle.fuel_type == fuel_type)
        if drive_type is not None:
            query = query.filter(Vehicle.drive_type == drive_type)
        if transmission is not None:
            query = query.filter(Vehicle.transmission == transmission)
            
        return query.all()

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()

    def get_all_active(self) -> List[Vehicle]:
        return self.db.query(Vehicle).filter(Vehicle.is_active).all()

    def update_vehicle(self, vehicle_id: int, update_data: Dict[str, Any]) -> Optional[Vehicle]:
        db_vehicle = self.get_by_id(vehicle_id)
        if db_vehicle:
            for key, value in update_data.items():
                if hasattr(db_vehicle, key):
                    setattr(db_vehicle, key, value)
            self.db.commit()
            self.db.refresh(db_vehicle)
        return db_vehicle

    def soft_delete_vehicle(self, vehicle_id: int) -> bool:
        db_vehicle = self.get_by_id(vehicle_id)
        if db_vehicle:
            db_vehicle.is_active = False
            self.db.commit()
            return True
        return False

    def get_years_by_model(self, model_id: int) -> List[int]:
        results = self.db.query(Vehicle.year).filter(
            Vehicle.model_id == model_id,
            Vehicle.is_active
        ).distinct().all()
        return [r[0] for r in results]

    def get_configs(self, model_id: int, year: int) -> List[Vehicle]:
        return self.db.query(Vehicle).filter(
            Vehicle.model_id == model_id,
            Vehicle.year == year,
            Vehicle.is_active
        ).all()

    def get_vehicle_id(self, model_id: int, year: int, engine: str) -> Optional[int]:
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.model_id == model_id,
            Vehicle.year == year,
            Vehicle.engine == engine,
            Vehicle.is_active
        ).first()
        return vehicle.vehicle_id if vehicle else None
