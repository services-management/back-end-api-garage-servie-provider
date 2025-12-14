from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Use AsyncSession if your DB is async
from typing import List
from uuid import UUID # Correct type for IDs

# --- Imports from your project ---
# Your Schemas (Pydantic Models for input/output)
from src.models.admin import AdminLogin, AdminCreate, AdminUpdate, AdminOut
from src.schemas.auth import Token
from src.models.technical import TechnicalCreate, TechnicalOut # Assuming you have a TechnicalOut
# Your Controller (Handles the business logic)
from src.controller.admin import AdminController
# Your Repositories (Used for dependency injection)
from src.repositories.admin import AdminRepository
from src.repositories.technical import TechnicalRepository
# Database dependency
from src.config.database import get_db # Assuming this function yields the session
from sqlalchemy.orm import Session
# --- Security Dependencies ---
from src.service.auth import create_access_token
# Assuming a function to verify the current admin user from JWT
from src.dependency.auth import get_current_admin_user 


# --- Router Initialization ---
router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
)

# --- Dependency Injection for Controller ---
def get_admin_controller(db:Session = Depends(get_db)):

    # 1. Instantiate Repositories

    admin_repo = AdminRepository(db)

    tech_repo = TechnicalRepository(db) 



    # 2. Instantiate the Controller, injecting ALL required Repositories

    controller_instance = AdminController(

        admin_repo=admin_repo,

        tech_repo=tech_repo # ✅ Inject Technical Repository

    ) 
    return controller_instance
# --- ENDPOINTS ---

## 1. Authentication Endpoints

@router.post("/login", response_model=Token, summary="Admin Login")
async def login_admin(
    admin_in: AdminLogin,
    controller: AdminController = Depends(get_admin_controller)
):
    """
    Authenticates an Admin user and returns a JWT token upon success.
    """
    admin = controller.authentication_admin(admin_in)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Payload for JWT: Use admin_id and role
    access_token = create_access_token(
        data={"sub": str(admin.admin_id), "role": admin.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


## 2. Admin Management Endpoints (Require Admin Authentication)

@router.get("/me", response_model=AdminOut, summary="Get Current Admin User Details")
async def read_admin_me(
    # The dependency ensures the user is logged in and populates the model
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves the details of the currently logged-in admin."""
    return current_admin


@router.post("/", response_model=AdminOut, status_code=status.HTTP_201_CREATED, summary="Create a new Admin")
async def create_new_admin(
    admin_in: AdminCreate,
    controller: AdminController = Depends(get_admin_controller),
    # Optional: Ensure only a super-admin or existing admin can create others
    current_admin: AdminOut = Depends(get_current_admin_user) 
):
    """Creates a new Admin account after performing unique username and contact checks."""
    return controller.create_admin(admin_in)


@router.put("/{admin_id}", response_model=AdminOut, summary="Update Admin Details")
async def update_existing_admin(
    admin_id: UUID, # Use UUID type for path parameter
    admin_in: AdminUpdate,
    controller: AdminController = Depends(get_admin_controller),
    # Authorization: Ensure only the admin or a super-admin can update
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Updates the details (username, password, email/phone) for a specific Admin."""
    
    # You might want to add a check here: if current_admin.admin_id != admin_id AND current_admin.role != "super_admin": raise 403
    
    return controller.update_admin(admin_id, admin_in)


## 3. Technical Account Provisioning Endpoint (Admin Function)

@router.post("/technical", response_model=TechnicalOut, status_code=status.HTTP_201_CREATED, summary="Provision Technical Account")
async def provision_technical_account(
    tech_in: TechnicalCreate,
    controller: AdminController = Depends(get_admin_controller),
    # Authorization: Must be an authenticated Admin to create a technical account
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Creates a new Technical staff account, checking for username/phone conflicts 
    across both Admin and Technical tables.
    """
    return controller.create_technical_account(tech_in)