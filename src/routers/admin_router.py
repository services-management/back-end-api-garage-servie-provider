
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from fastapi import Query   
# Database dependency
from src.config.database import \
    get_db  # Assuming this function yields the session
# Your Controller (Handles the business logic)
from src.controller.admin_controller import AdminController
# Assuming a function to verify the current admin user from JWT
from src.dependency.auth import get_current_admin_user
# --- Imports from your project ---
# Your Schemas (Pydantic Models for input/output)
from src.models.admin_model import (AdminCreate, AdminLogin, AdminOut,
                                    AdminUpdate, InvoiceUpload)
from src.models.booking_model import BookingCreate, BookingHistoryResponse
from src.models.technical_model import (  # Assuming you have a TechnicalOut
    TechnicalCreate, TechnicalOut)
from src.models.booking_model import BookingStatus
# Your Repositories (Used for dependency injection)
from src.repositories.admin_repositories import AdminRepository
from src.repositories.technical_repositorie import TechnicalRepository
from src.repositories.booking_repositories import BookingRepository
from src.schemas.auth import Token
from src.models.admin_model import RejectBookingRequest, AssignTeamRequest
# --- Security Dependencies ---
from src.service.auth import create_access_token
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

    booking_repo = BookingRepository(db)

    # 2. Instantiate the Controller, injecting ALL required Repositories

    controller_instance = AdminController(

        db=db,

        admin_repo=admin_repo,

        tech_repo=tech_repo, # ✅ Inject Technical Repository

        booking_repo=booking_repo  # ✅ Inject Booking Repository

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


@router.put("/me", response_model=AdminOut, summary="Update current Admin Details")
async def update_existing_admin(
    admin_in: AdminUpdate,
    controller: AdminController = Depends(get_admin_controller),
    # Authorization: Ensure only the admin or a super-admin can update
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Updates the details (username, password, email/phone) for a specific Admin."""
    
    # You might want to add a check here: if current_admin.admin_id != admin_id AND current_admin.role != "super_admin": raise 403
    
    return controller.update_admin(current_admin.admin_id, admin_in)


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

@router.get("/bookings", response_model=List[BookingHistoryResponse], summary="Search and Filter Bookings")
async def search_bookings(
    query: Optional[str] = Query(None, description="Search by name, phone, or car model"),
    status: Optional[BookingStatus] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    The main endpoint for the Admin UI Table. 
    Allows admins to search for customers and filter by status.
    """
    return await controller.get_all_bookings_filtered(
        query=query, 
        status=status, 
        limit=limit
    )

@router.get("/overview",summary="Get Daily Dashboard Overview")
async def daily_overview(
    target_date: date = Query(default=date.today()),
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Get stats and booking list for a specific day"""
    return await service.get_daily_overview(target_date)

@router.post("/bookings/{booking_id}/accept",summary="Accept Booking")
async def accept(
    booking_id: int, 
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)):
    """Confirm a pending booking"""
    return await service.accept_booking(booking_id)

@router.post("/bookings/{booking_id}/reject",summary="Reject Booking")
async def reject(
    booking_id: int, 
    payload: RejectBookingRequest, 
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Cancel a booking with a custom reason sent to the user"""
    return await service.reject_booking(booking_id, payload.reason)


@router.post("/bookings", response_model=BookingHistoryResponse, status_code=status.HTTP_201_CREATED, summary="Create a Booking for a Customer")
async def create_booking_for_customer(
    booking_data: BookingCreate,
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Allows an admin to create a booking on behalf of a customer.
    The 'source' will be automatically set to 'PHONE'.
    """
    return await service.create_booking_for_customer(booking_data)



@router.post("/bookings/{booking_id}/invoice", status_code=status.HTTP_201_CREATED, summary="Upload an Invoice for a Booking")
async def upload_invoice(
    booking_id: int,
    invoice_data: InvoiceUpload,
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Uploads an invoice URL for a completed booking.
    """
    return await service.upload_invoice_for_booking(booking_id, invoice_data)


@router.post("/bookings/{booking_id}/assign")
async def assign(
    booking_id: int, 
    payload: AssignTeamRequest, 
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Assign a specific technical team to a car"""
    return await service.assign_team(booking_id, payload.technical_team_id)