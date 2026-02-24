from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload
from src.schemas.vehicle import Vehicle,Make,Model  # Corrected imports

class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- READ (Individual & Hierarchical) ---
    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """Fetch vehicle with nested Model and Make names."""
        stmt = (
            select(Vehicle)
            .options(joinedload(Vehicle.model).joinedload(Model.make))
            .where(Vehicle.vehicle_id == vehicle_id)
        )
        return self.db.execute(stmt).scalars().first()

    def get_all_makes(self) -> List[Make]:
        """Standard 'Step 1' for the Oil Finder: Get all brands."""
        stmt = select(Make).where(Make.is_active).order_by(Make.name)
        return list(self.db.execute(stmt).scalars().all())
    
    def get_make_by_id(self, make_id: int) -> Optional[Make]:
        """Fetch a specific brand by its primary key."""
        stmt = select(Make).where(Make.id == make_id)
        return self.db.execute(stmt).scalars().first()

    def get_make_by_name(self, name: str) -> Optional[Make]:
        """Find a brand by name (Case-Insensitive) for duplicate checks."""
        stmt = select(Make).where(Make.name.ilike(name))
        return self.db.execute(stmt).scalars().first()

    def get_model_by_id(self,id:int)-> Optional[Model]:
        """Find a model by id"""
        stmt = select(Model).where(Model.id == id)
        return self.db.execute(stmt).scalars().first()
    
    def get_make_id_by_name(self, name: str) -> Optional[int]:
        """Fetch only the ID for a given brand name."""
        stmt = select(Make.id).where(Make.name.ilike(name))
        return self.db.execute(stmt).scalars().first()
    
    def get_models_by_make(self, make_id: int):
        """Standard 'Step 2': Get models for the chosen brand."""
        stmt = (
            select(Model)
            .where(Model.make_id == make_id, Model.is_active)
            .order_by(Model.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_years_by_model(self, model_id: int):
        """Standard 'Step 3': Get years for the chosen model."""
        stmt = (
            select(Vehicle.year)
            .where(Vehicle.model_id == model_id, Vehicle.is_active)
            .distinct()
            .order_by(Vehicle.year.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def filter_vehicles(self, model_id: int, year: int):
        """Final Step: Get the exact engine configurations."""
        stmt = (
            select(Vehicle)
            # Efficiently load Model AND Make names in one query
            .options(joinedload(Vehicle.model).joinedload(Model.make))
            .where(
                Vehicle.model_id == model_id, 
                Vehicle.year == year, 
                Vehicle.is_active
            )
        )
        return list(self.db.execute(stmt).scalars().all())
    
    # --- CREATE (Handling Relationships) ---
    def create_make(self, name: str) -> Make:
        """Create a new car brand (e.g., Toyota, BMW)."""
        db_make = Make(name=name, is_active=True)
        self.db.add(db_make)
        self.db.commit()
        self.db.refresh(db_make)
        return db_make

    def create_model(self, make_id: int, name: str) -> Model:
        """Create a model tied to a specific make (e.g., Corolla tied to Toyota)."""
        db_model = Model(make_id=make_id, name=name, is_active=True)
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return db_model
    
    def create_vehicle(self, model_id: int, **kwargs):
        """Create a vehicle config tied to a specific model ID."""
        db_vehicle = Vehicle(model_id=model_id, **kwargs)
        self.db.add(db_vehicle)
        self.db.commit()
        self.db.refresh(db_vehicle)
        return db_vehicle
    
    def update_make(self, make_id: int,name:str) -> Optional[Make]:
        """Update a brand name in the database."""
        stmt = update(Make).where(Make.id == make_id).values(name=name)
        self.db.execute(stmt)
        self.db.commit()
        return self.get_make_by_id(make_id)

    def update_model(self, model_id: int, name: str) -> Optional[Model]:
        """Update a model name in the database."""
        stmt = update(Model).where(Model.id == model_id).values(name=name)
        self.db.execute(stmt)
        self.db.commit()
        return self.get_model_by_id(model_id)

    def update_vehicle(self, vehicle_id: int, update_data: dict) -> Optional[Vehicle]:
        """Update specific fields of a vehicle configuration."""
        if not update_data:
            return self.get_by_id(vehicle_id)
            
        stmt = (
            update(Vehicle)
            .where(Vehicle.vehicle_id == vehicle_id)
            .values(**update_data)
        )
        self.db.execute(stmt)
        self.db.commit()
        return self.get_by_id(vehicle_id)
    
    # soft delete 
    def soft_delete_vehicle(self, vehicle_id: int) -> bool:
        """Hide a specific engine/year configuration."""
        stmt = update(Vehicle).where(Vehicle.vehicle_id == vehicle_id).values(is_active=False)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def soft_delete_model(self, model_id: int) -> bool:
        """Hide an entire model line."""
        stmt = update(Model).where(Model.id == model_id).values(is_active=False)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def soft_delete_make(self, make_id: int) -> bool:
        """Hide an entire brand."""
        stmt = update(Make).where(Make.id == make_id).values(is_active=False)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0