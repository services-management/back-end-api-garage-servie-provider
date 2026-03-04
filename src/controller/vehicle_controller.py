# src/controller/vehicle_controller.py

from sqlalchemy.orm import Session
from src.repositories.vehicle_repository import VehicleRepository
from src.models.vehicle_model import VehicleCreate, Makecreate, Modelcreate

class Vehiclecontroller:
    def __init__(self, db: Session):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)

    # ==================== OIL FINDER LOGIC ====================

    def get_makes_for_finder(self):
        return self.vehicle_repo.get_all_makes(active_only=True)

    def get_models_for_finder(self, make_id: int):
        return self.vehicle_repo.get_models_by_make(make_id, active_only=True)

    def get_years_for_finder(self, model_id: int):
        return self.vehicle_repo.get_years_by_model(model_id)

    def get_final_configurations(self, model_id: int, year: int):
        return self.vehicle_repo.get_configs(model_id, year)

    # ==================== ADMIN ACTIONS ====================

    def create_new_make(self, make_data: Makecreate):
        # 1. Unique check
        if self.vehicle_repo.get_make_by_name(make_data.name):
            raise ValueError(f"Make '{make_data.name}' already exists.")
        return self.vehicle_repo.create_make(make_data.name)

    def create_new_model(self, model_data: Modelcreate):
        # 1. Verify make exists by name (since schema uses make: Makecreate)
        parent_make = self.vehicle_repo.get_make_by_name(model_data.make.name)
        if not parent_make:
            raise ValueError(f"Make '{model_data.make.name}' not found.")
        return self.vehicle_repo.create_model(parent_make.id, model_data.name)

    def create_new_vehicle(self, vehicle_data: VehicleCreate):
        # 1. Verify model exists
        if not self.vehicle_repo.get_model_by_id(vehicle_data.model_id):
            raise ValueError(f"Model ID {vehicle_data.model_id} not found.")
        
        return self.vehicle_repo.create_vehicle(
            model_id=vehicle_data.model_id,
            year=vehicle_data.year,
            engine=vehicle_data.engine,
            v_type=vehicle_data.vehicle_type,
            f_type=vehicle_data.fuel_type,
            d_type=vehicle_data.drive_type,
            trans=vehicle_data.transmission
        )

    def update_existing_make(self, make_id: int, name: str):
        updated = self.vehicle_repo.update_make(make_id, name)
        if not updated:
            raise ValueError("Make not found")
        return updated

    def update_existing_model(self, model_id: int, name: str):
        updated = self.vehicle_repo.update_model(model_id, name)
        if not updated:
            raise ValueError("Model not found")
        return updated
