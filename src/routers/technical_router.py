from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

# --- Imports from your project ---
# Schemas (Pydantic Models)
from src.models.technical_model import TechnicalLogin, TechnicalOut, TechnicalUpdate, TechnicalStatusUpdate
from src.schemas.auth import Token # Token model is reused
# Controller & Repositories
from src.controller.technical_controller import TechnicalController # <-- ASSUMPTION: You need this controller
from src.repositories.technical_repositorie import TechnicalRepository
# Database dependency
from src.config.database import get_db
# Security/Auth Utilities
from src.service.auth import create_access_token # JWT creation utility
from src.dependency.auth import get_current_technical_user # <-- ASSUMPTION: You need this dependency

# --- Router Initialization ---
router = APIRouter(
    prefix="/technical",
    tags=["Technical Staff"],
)

# --- Dependency Injection for Controller ---
# ASSUMPTION: TechnicalController primarily depends on TechnicalRepository
def get_technical_controller(db: Session = Depends(get_db)) -> TechnicalController:
    tech_repo = TechnicalRepository(db)
    # NOTE: If your controller needs other repos (e.g., TicketRepo), inject them here.
    return TechnicalController(tech_repo=tech_repo)

# --- ENDPOINTS ---

## 1. Authentication (Public)

@router.post("/login", response_model=Token, summary="Technical Staff Login")
def login_technical(
    tech_in: TechnicalLogin,
    controller: TechnicalController = Depends(get_technical_controller)
):
    """
    Authenticates a Technical staff member and returns a JWT token.
    """
    technical_user = controller.authenticate_technical(tech_in)
    if not technical_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Payload for JWT: Use technical_id and role
    # Note: Ensure the role is "technical"
    access_token = create_access_token(
        data={"sub": str(technical_user.technical_id), "role": technical_user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


## 2. Technical Self-Management (Requires Technical Auth)

@router.get("/me", response_model=TechnicalOut, summary="Get Current Technical User Details")
def read_technical_me(
    #  SECURE: Dependency verifies JWT and fetches the user object
    current_user: TechnicalOut = Depends(get_current_technical_user)
):
    """Retrieves the details of the currently logged-in technical staff."""
    return current_user

@router.put("/me", response_model=TechnicalOut, summary="Update My Technical User Details")
def update_technical_me(
    # Remove technical_id from path parameters
    tech_in: TechnicalUpdate,
    controller: TechnicalController = Depends(get_technical_controller),
    current_user: TechnicalOut = Depends(get_current_technical_user)
):
    """Allows the currently logged-in technical user to update their own details (name, phone, password)."""
    
    # 1. We strictly use the ID from the validated JWT token (current_user.id)
    # 2. We pass this ID and the update data to the controller
    # This prevents a malicious user from setting the URL to /technical/someones_id
    return controller.update_technical_user(current_user.technical_id, tech_in)

@router.patch("/me/status", response_model=TechnicalOut, summary="Update Technical Status")
def update_technical_status(
    status_in: TechnicalStatusUpdate,
    controller: TechnicalController = Depends(get_technical_controller),
    current_user: TechnicalOut = Depends(get_current_technical_user)
):
    """Allows a technical user to change their operational status (e.g., Free, Busy, off_duty)."""
    # The controller logic will validate the status change and update the DB
    return controller.update_technical_status(current_user.technical_id, status_in.status)