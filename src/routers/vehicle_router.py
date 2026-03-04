from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.repositories.vehicle_repository import VehicleRepository
from src.controller.vehicle_controller import Vehiclecontroller
from src.models.vehicle_model import (
    VehicleCreate, MakeBase, ModelBase, VehicleBase, 
    Modelupdate, Makeupdate, Makecreate, Modelcreate
)
from src.models.admin_model import AdminOut
from src.dependency.auth import get_current_admin_user

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

# Dependency Injection helpers
def get_repo(db: Session = Depends(get_db)) -> VehicleRepository:
    return VehicleRepository(db)

def get_controller(db: Session = Depends(get_db)) -> Vehiclecontroller:
    return Vehiclecontroller(db)

# ==================== PUBLIC ====================

@router.get("/makes", response_model=List[MakeBase])
def get_all_makes(controller: Vehiclecontroller = Depends(get_controller)):
    return controller.get_makes_for_finder()

@router.get("/makes/{make_id}/models", response_model=List[ModelBase])
def get_models_by_make(make_id: int, controller: Vehiclecontroller = Depends(get_controller)):
    models = controller.get_models_for_finder(make_id)
    if not models:
        raise HTTPException(status_code=404, detail="No active models found for this make")
    return models

@router.get("/models/{model_id}/years", response_model=List[int])
def get_years_by_model(model_id: int, controller: Vehiclecontroller = Depends(get_controller)):
    years = controller.get_years_for_finder(model_id)
    if not years:
        raise HTTPException(status_code=404, detail="No active years found for this model")
    return years

@router.get("/filter", response_model=List[VehicleBase])
def get_vehicle_configurations(model_id: int, year: int, controller: Vehiclecontroller = Depends(get_controller)):
    return controller.get_final_configurations(model_id, year)

# ==================== ADMIN ====================

@router.post("/", response_model=VehicleBase, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate, 
    controller: Vehiclecontroller = Depends(get_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    try:
        return controller.create_new_vehicle(vehicle_data=vehicle_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/make", response_model=MakeBase, status_code=status.HTTP_201_CREATED)
def create_make(
    make_in: Makecreate,
    controller: Vehiclecontroller = Depends(get_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    try:
        return controller.create_new_make(make_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/model", response_model=ModelBase, status_code=status.HTTP_201_CREATED)
def create_model(
    model_in: Modelcreate,
    controller: Vehiclecontroller = Depends(get_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    try:
        return controller.create_new_model(model_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/all", response_model=List[VehicleBase])
def get_all_vehicles(
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    return repo.get_all_active()

@router.get("/{vehicle_id}", response_model=VehicleBase)
def get_vehicle_details(vehicle_id: int, repo: VehicleRepository = Depends(get_repo)):
    vehicle = repo.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.patch("/make/{make_id}", response_model=MakeBase)
def update_make(
    make_id: int,
    make_update: Makeupdate,
    controller: Vehiclecontroller = Depends(get_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    try:
        return controller.update_existing_make(make_id, make_update.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/model/{model_id}", response_model=ModelBase)
def update_model(
    model_id: int,
    model_update: Modelupdate,
    controller: Vehiclecontroller = Depends(get_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    try:
        return controller.update_existing_model(model_id, model_update.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/make/{make_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_make(
    make_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    if not repo.soft_delete_make(make_id):
        raise HTTPException(status_code=404, detail="Make not found")
    return None

@router.delete("/model/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    if not repo.soft_delete_model(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    return None

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int, 
    repo: VehicleRepository = Depends(get_repo),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    if not repo.soft_delete_vehicle(vehicle_id):
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None
