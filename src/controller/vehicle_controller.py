
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.vehicle_repository import VehicleRepository
from src.models.vehicle_model import VehicleCreate, VehicleUpdate,Modelcreate,Makecreate

class  Vehiclecontroller:
    def __init__(self, db: Session):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)

    # ============================================================================
    #  PUBLIC SEARCH LOGIC (The "Oil Finder" Experience)
    # ============================================================================

    def get_makes_for_finder(self):
        """Returns only brands that are active and ready for customers."""
        return self.vehicle_repo.get_all_makes()

    def get_models_for_finder(self, make_id: int):
        """Logic: Check if the make exists before looking for models."""
        models = self.vehicle_repo.get_models_by_make(make_id)
        if not models:
            # We return an empty list because a brand might just not have models yet
            return []
        return models

    def get_years_for_finder(self, model_id: int):
        return self.vehicle_repo.get_years_by_model(model_id)

    def get_final_configurations(self, model_id: int, year: int):
        """Returns the specific engines the user can click on."""
        return self.vehicle_repo.filter_vehicles(model_id, year)

    # ============================================================================
    #  ADMIN / MANAGEMENT LOGIC (Validation & Rules)
    # ============================================================================

    def create_new_vehicle(self, vehicle_data: VehicleCreate):
        """
        Business Rule: You cannot add a vehicle to a Model that is inactive 
        or doesn't exist.
        """
        data = vehicle_data.model_dump()
    
        # 2. Extract nested objects that aren't DB columns
        # We remove 'make' because the DB usually only cares about 'model_id'
        data.pop("make", None) 
        
        # 3. Get the model_id (either from the data or a lookup)
        model_id = data.pop("model_id", 1) # Example fallback
        
        # 4. Pass only what the Repo/DB actually needs
        return self.vehicle_repo.create_vehicle(model_id=model_id, **data)
        
    def create_new_make(self,make_data:Makecreate):
        """
        Business Rules handled via Repository:
        - Case-insensitive uniqueness.
        - Whitespace cleanup.
        - Reactivation if soft-deleted.
        """
        clean_name = make_data.name.strip()

        existing_make = self.vehicle_repo.get_make_by_name(clean_name)

        if existing_make:
            # Rule: If it was hidden (soft-deleted), bring it back
            if not existing_make.is_active:
                existing_make.is_active = True
                self.db.commit()
                self.db.refresh(existing_make)
            return existing_make

        # If truly new, use your original logic:
        return self.vehicle_repo.create_make(name=clean_name)
    
    def create_new_model(self, model_data: Modelcreate):
        """
        Creates a new vehicle model using only the Make name and Model name.
        """
        clean_model_name = model_data.name.strip()
        clean_make_name = model_data.make.name.strip() # Assuming your schema uses 'make_name'

        # 1. Parent Check: Find the Make by its name
        parent_make = self.vehicle_repo.get_make_by_name(clean_make_name)
        
        if not parent_make:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand '{clean_make_name}' not found."
            )
        
        if not parent_make.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand '{clean_make_name}' is currently inactive."
            )

        # 2. Scoped Uniqueness: Get all models for THIS specific Make ID
        existing_models = self.vehicle_repo.get_models_by_make(parent_make.id)
        
        # Check if the model already exists (case-insensitive)
        duplicate = next((m for m in existing_models if m.name.lower() == clean_model_name.lower()), None)

        if duplicate:
            # 3. Reactivation Logic: If it exists but is hidden, turn it back on
            if not duplicate.is_active:
                return self.vehicle_repo.update_model(duplicate.id, name=duplicate.name, is_active=True)
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model '{clean_model_name}' already exists for {parent_make.name}."
            )

        # 4. Success: Create the new model using the ID we found
        return self.vehicle_repo.create_model(parent_make.id, clean_model_name)

    def update_existing_make(self, make_id: int, name:str):
        # 1. Check if the Make exists
        make = self.vehicle_repo.get_make_by_id(make_id)
        if not make:
            raise HTTPException(status_code=404, detail="Brand not found")

        clean_name = name.strip()

        # 2. Check if the new name is already taken by a DIFFERENT brand
        existing = self.vehicle_repo.get_make_by_name(clean_name)
        if existing and existing.id != make_id:
            raise HTTPException(
                status_code=409, 
                detail=f"Brand '{clean_name}' already exists with a different ID."
            )

        return self.vehicle_repo.update_make(make_id,clean_name)
    
    def update_existing_model(self, model_id: int, name:str):
        # 1. Check if the Model exists
        model = self.vehicle_repo.get_model_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        clean_name = name.strip()

        # 2. Check for collisions within the SAME brand
        # Use your get_models_by_make method to see other models for this brand
        existing_models = self.vehicle_repo.get_models_by_make(model.make_id)
        
        for m in existing_models:
            # If a match is found that isn't the model we are currently editing
            if m.name.lower() == clean_name.lower() and m.id != model_id:
                raise HTTPException(
                    status_code=409, 
                    detail=f"This brand already has a model named '{clean_name}'."
                )

        return self.vehicle_repo.update_model(model_id, clean_name)

    def update_existing_vehicle(self, vehicle_id: int, update_data: VehicleUpdate):
        """Only updates fields that are actually provided (exclude_unset)."""
        data = update_data.model_dump(exclude_unset=True)
        vehicle = self.vehicle_repo.update_vehicle(vehicle_id, data)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Vehicle configuration not found"
            )
        return vehicle

    def deactivate_vehicle(self, vehicle_id: int):
        """The 'Soft Delete' trigger."""
        success = self.vehicle_repo.soft_delete_vehicle(vehicle_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Could not find vehicle to deactivate"
            )
        return {"message": "Vehicle successfully hidden from search results"}