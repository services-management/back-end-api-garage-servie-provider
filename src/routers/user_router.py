from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.controller.user_controller import UserService
from src.dependency.auth import get_current_customer
from src.models.user_model import (
    UserResponse, 
    UserUpdate, 
    UserPasswordUpdate, 
    CustomerVehicleCreate, 
    CustomerVehicleResponse,
    CustomerVehicleUpdate
)
from typing import List

router = APIRouter(prefix="/users", tags=["User Profile"])

def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: UserResponse = Depends(get_current_customer)):
    """Retrieve current user profile information."""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserUpdate,
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Update user's basic profile details (full_name)."""
    updated_user = await service.update_profile(current_user.user_id, payload.full_name)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.post("/me/setup-password", status_code=status.HTTP_200_OK)
async def setup_password(
    payload: UserPasswordUpdate,
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Allow a user (who logged in via OTP) to set their password for the first time."""
    # Note: UserPasswordUpdate has new_password and confirm_password
    success = await service.set_password(current_user.user_id, payload.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set password")
    return {"message": "Password setup successfully"}

@router.get("/me/full-profile")
async def get_detailed_profile(
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Returns profile details, linked cars, and booking summary."""
    return service.get_profile_with_history(current_user.user_id)

# --- Vehicle Management for Customers ---

@router.post("/me/vehicles", response_model=CustomerVehicleResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    payload: CustomerVehicleCreate,
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Add a new vehicle to user's profile."""
    return await service.add_vehicle(current_user.user_id, payload)

@router.get("/me/vehicles", response_model=List[CustomerVehicleResponse])
async def get_my_vehicles(
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """List all vehicles in user's profile."""
    return await service.get_my_vehicles(current_user.user_id)

@router.patch("/me/vehicles/{vehicle_id}", response_model=CustomerVehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    payload: CustomerVehicleUpdate,
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Update a vehicle in user's profile."""
    updated_vehicle = await service.update_vehicle(current_user.user_id, vehicle_id, payload)
    if not updated_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return updated_vehicle

@router.delete("/me/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle(
    vehicle_id: int,
    current_user: UserResponse = Depends(get_current_customer),
    service: UserService = Depends(get_user_service)
):
    """Delete a vehicle from user's profile."""
    success = await service.delete_vehicle(current_user.user_id, vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None
