from uuid import UUID  # Correct type for IDs
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date
from fastapi import Query   
# Database dependency
from src.config.database import \
    get_db  # Assuming this function yields the session
# Your Controller (Handles the business logic)
from src.controller.admin_controller import AdminController
# S3 Service for file uploads
from src.service.s3_service import S3Service, get_s3_service
# Assuming a function to verify the current admin user from JWT
from src.dependency.auth import get_current_admin_user
# --- Imports from your project ---
# Your Schemas (Pydantic Models for input/output)
from src.models.admin_model import (AdminCreate, AdminLogin, AdminOut,
                                    AdminUpdate, InvoiceUpload)
from src.models.booking_model import (AdminBookingCreate, BookingHistoryResponse)
from src.models.technical_model import (  # Assuming you have a TechnicalOut
    TechnicalCreate, TechnicalOut, TechnicalTeamCreate, TechnicalTeamOut)
from src.models.booking_model import BookingStatus
# Your Repositories (Used for dependency injection)
from src.repositories.admin_repositories import AdminRepository
from src.repositories.technical_repositorie import TechnicalRepository
from src.repositories.booking_repositories import BookingRepository
from src.schemas.auth import Token
from src.models.admin_model import RejectBookingRequest, AssignTeamRequest
# --- Security Dependencies ---
from src.service.auth import create_token_pair, ACCESS_TOKEN_EXPIRE_MINUTES
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
    Authenticates an Admin user and returns JWT access and refresh tokens upon success.
    """
    admin = controller.authentication_admin(admin_in)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Payload for JWT: Use admin_id and role
    token_data = {"sub": str(admin.admin_id), "role": admin.role}
    access_token, refresh_token = create_token_pair(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


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

@router.get("/bookings/{booking_id}", response_model=BookingHistoryResponse, summary="Get Booking by ID")
async def get_booking(
    booking_id: int,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Get detailed information about a specific booking by ID.
    Includes customer info, items, services, and products.
    """
    return await controller.get_booking_by_id(booking_id)

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
    booking_data: AdminBookingCreate,
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Allows an admin to create a booking on behalf of a customer.
    The 'source' will be automatically set to 'PHONE'.
    """
    return await service.create_booking_for_customer(booking_data)


@router.post("/bookings/{booking_id}/invoice/upload-file", status_code=status.HTTP_201_CREATED, summary="Upload Invoice File to S3")
async def upload_invoice_file(
    booking_id: int,
    file: UploadFile = File(..., description="Invoice file (PDF, JPG, PNG, max 10MB)"),
    service: AdminController = Depends(get_admin_controller),
    s3_service: S3Service = Depends(get_s3_service),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Uploads invoice file directly to S3 storage and notifies customer via Telegram.
    
    Supported formats: PDF, JPG, PNG, JPEG, WEBP
    Max file size: 10MB
    """
    import os
    from datetime import datetime
    
    # First validate booking exists and is completed BEFORE reading file or uploading to S3
    # This ensures we return 400 for invalid bookings, not 500
    await service.upload_invoice_for_booking(
        booking_id, 
        InvoiceUpload(external_invoice_url="validation-only-temp")
    )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10MB"
        )
    
    # Get file extension - handle tuple case from TestClient
    filename = file.filename if isinstance(file.filename, str) else ""
    _, file_ext = os.path.splitext(filename.lower())
    if not file_ext:
        file_ext = ".pdf"  # Default to PDF
    
    # Upload to S3
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"invoice_booking_{booking_id}_{timestamp}{file_ext}"
    s3_key = f"invoices/{safe_filename}"
    
    # Determine content type
    content_type_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }
    content_type = content_type_map.get(file_ext, "application/pdf")
    
    # Upload using S3 service
    invoice_url = s3_service.upload_file_from_bytes(
        file_bytes=file_content,
        s3_key=s3_key,
        content_type=content_type
    )
    
    if not invoice_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload invoice to S3 storage"
        )
    
    # Create invoice data object with actual S3 URL and notify customer (second call)
    invoice_upload_data = InvoiceUpload(external_invoice_url=invoice_url)
    
    return await service.upload_invoice_for_booking(booking_id, invoice_upload_data)

@router.post("/bookings/{booking_id}/assign")
async def assign(
    booking_id: int, 
    payload: AssignTeamRequest, 
    service: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Assign a specific technical team to a car"""
    return await service.assign_team(booking_id, payload.technical_team_id)

## 4. Account Management Endpoints (Admin Function)

@router.get("/accounts/admins", response_model=List[AdminOut], summary="List all Admin accounts")
async def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves a list of all Admin accounts."""
    return controller.get_all_admins(skip=skip, limit=limit)

@router.get("/accounts/technicals", response_model=List[TechnicalOut], summary="List all Technical accounts")
async def list_technicals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves a list of all Technical accounts."""
    return controller.get_all_technicals(skip=skip, limit=limit)

@router.put("/accounts/admins/{admin_id}/deactivate", response_model=AdminOut, summary="Deactivate an Admin account")
async def deactivate_admin_acc(
    admin_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Deactivates an Admin account by setting is_active to False."""
    if current_admin.admin_id == admin_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account.")
    return controller.deactivate_admin(admin_id)

@router.put("/accounts/technicals/{technical_id}/deactivate", response_model=TechnicalOut, summary="Deactivate a Technical account")
async def deactivate_technical_acc(
    technical_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Deactivates a Technical account by setting is_active to False."""
    return controller.deactivate_technical(technical_id)


@router.get("/accounts/admins/{admin_id}/magic-link", summary="Get admin Telegram magic link")
async def get_admin_magic_link(
    admin_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves the Telegram magic link for an admin account."""
    return controller.get_admin_magic_link(admin_id)


@router.get("/accounts/technicals/{technical_id}/magic-link", summary="Get technical Telegram magic link")
async def get_technical_magic_link(
    technical_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves the Telegram magic link for a technical account."""
    return controller.get_technical_magic_link(technical_id)


## 5. Technical Team Management Endpoints

@router.post("/teams", response_model=TechnicalTeamOut, status_code=status.HTTP_201_CREATED, summary="Create Technical Team")
async def create_technical_team(
    team_in: TechnicalTeamCreate,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Creates a new technical team.
    Team lead can be assigned later if not provided.
    """
    return await controller.create_new_team(team_in)


@router.get("/teams", response_model=List[TechnicalTeamOut], summary="List all Technical Teams")
async def list_technical_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """Retrieves a list of all technical teams."""
    return await controller.list_all_teams(skip=skip, limit=limit)


@router.post("/teams/{team_id}/members/{technical_id}", response_model=TechnicalOut, summary="Add Member to Team")
async def add_member_to_team(
    team_id: UUID,
    technical_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Assigns a technical staff member to a specific team.
    """
    return await controller.add_staff_to_team(technical_id, team_id)


@router.delete("/teams/members/{technical_id}", response_model=TechnicalOut, summary="Remove Member from Team")
async def remove_member_from_team(
    technical_id: UUID,
    controller: AdminController = Depends(get_admin_controller),
    current_admin: AdminOut = Depends(get_current_admin_user)
):
    """
    Removes a technical staff member from their current team.
    The staff member remains active but is no longer assigned to any team.
    """
    return await controller.remove_staff_from_team(technical_id)
