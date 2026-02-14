from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.repositories.vehicle_repository import VehicleRepository
from src.controller.vehicle_controller import Vehiclecontroller
from src.models.vehicle_model import VehicleCreate,MakeBase,ModelBase,VehicleUpdate,VehicleBase,Modelupdate,Makeupdate,Makecreate,Modelcreate
from src.models.admin_model import AdminOut
from src.dependency.auth import get_current_admin_user
router = APIRouter(prefix = "/vehicles", tags=["Vehicles"])

# Dependency Injection helper
def get_repo(db:Session = Depends(get_db)) -> VehicleRepository:
    return VehicleRepository(db)

def get_repository(db: Session = Depends(get_db)) -> Vehiclecontroller:
    return Vehiclecontroller(db)

# ============================================================================
#  PART 1: THE OIL FINDER (Public Search Flow)
# ============================================================================

@router.get("/makes", response_model=List[MakeBase])
def get_all_makes(repo: Vehiclecontroller = Depends(get_repository)):
    """
    Step 1: Returns a list of all active car brands (e.g., Toyota, BMW).
    """
    return repo.get_makes_for_finder()

@router.get("/makes/{make_id}/models", response_model=List[ModelBase])
def get_models_by_make(
    make_id: int, 
    repo: Vehiclecontroller = Depends(get_repository)
):
    """
    Step 2: Returns models for a specific brand (e.g., Select Toyota -> Get Camry, Corolla).
    """
    models = repo.get_models_for_finder(make_id)
    if not models:
        raise HTTPException(status_code=404, detail="No active models found for this make")
    return models

@router.get("/models/{model_id}/years", response_model=List[int])
def get_years_by_model(
    model_id: int, 
    repo: Vehiclecontroller = Depends(get_repository)
):
    """
    Step 3: Returns available years for a specific model (e.g., Select Camry -> Get 2022, 2021).
    """
    years = repo.get_years_for_finder(model_id)
    if not years:
        raise HTTPException(status_code=404, detail="No active years found for this model")
    return years

@router.get("/filter", response_model=List[VehicleBase])
def get_vehicle_configurations(
    model_id: int, 
    year: int, 
    repo: Vehiclecontroller = Depends(get_repository)
):
    """
    Step 4: Returns the specific engine configurations (e.g., 2.5L Hybrid, 3.5L V6).
    The user clicks one of these to see the compatible oils.
    """
    vehicles = repo.get_final_configurations(model_id, year)
    if not vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found for this configuration")
    return vehicles

# ============================================================================
#  PART 2: ADMIN MANAGEMENT (Dashboard Only)
# ============================================================================

@router.post("/", response_model=VehicleBase, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate, 
    repo: Vehiclecontroller = Depends(get_repository),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """Admin: Add a new vehicle configuration to the database."""
    return repo.create_new_vehicle(vehicle_data=vehicle_in)

@router.post("/make",response_model=MakeBase, status_code=status.HTTP_201_CREATED)
def create_make(
    make:Makecreate,
    repo: Vehiclecontroller = Depends(get_repository),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """Admin : add new make"""
    return repo.create_new_make(make)

@router.post("/model",response_model=ModelBase, status_code=status.HTTP_201_CREATED)
def create_model(
    model:Modelcreate,
    repo: Vehiclecontroller = Depends(get_repository),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """admin : add new model"""
    return repo.create_new_model(model)

@router.get("/{vehicle_id}", response_model=VehicleBase)
def get_vehicle_details(
    vehicle_id: int, 
    repo: VehicleRepository = Depends(get_repo)
):
    """Admin/Public: Get full details of a single vehicle ID."""
    vehicle = repo.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.patch("/make/{make_id}", response_model=Makeupdate)
def update_make(
    id :int,
    make_update: Makeupdate,
    repo:Vehiclecontroller = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    return repo.update_existing_make(id,make_update.name)

@router.patch("/model/{vehicle_id}", response_model=Modelupdate)
def update_model(
    id :int,
    make_update: Modelupdate,
    repo:Vehiclecontroller = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    return repo.update_existing_make(id,make_update.name)

@router.patch("/{vehicle_id}", response_model=VehicleBase)
def update_vehicle(
    vehicle_id: int, 
    vehicle_update: VehicleUpdate, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """Admin: Update details (e.g., fix a typo in engine name)."""
    vehicle = repo.update_vehicle(vehicle_id, vehicle_update.model_dump(exclude_unset=True))
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """
    Admin: Soft delete a vehicle. 
    It will no longer appear in the Oil Finder but remains in the DB history.
    """
    success = repo.soft_delete_vehicle(vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """
    Admin: Soft delete a model. 
    It will no longer appear in the Oil Finder but remains in the DB history.
    """
    success = repo.soft_delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None

@router.delete("/{make_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_make(
    make_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """
    Admin: Soft delete a make. 
    It will no longer appear in the Oil Finder but remains in the DB history.
    """
    success = repo.soft_delete_make(make_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None
