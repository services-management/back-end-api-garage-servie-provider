from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Database dependency
from src.config.database import get_db
# Controller & Repositories
from src.controller.technical_controller import \
    TechnicalController  # <-- ASSUMPTION: You need this controller
from src.dependency.auth import \
    get_current_technical_user, get_current_user_admin_or_technical, get_current_admin_user  # <-- ASSUMPTION: You need this dependency
# --- Imports from your project ---
# Schemas (Pydantic Models)
from src.models.technical_model import (TechnicalLogin, TechnicalOut,
                                        TechnicalStatusUpdate, TechnicalUpdate,
                                        TechnicalPerformance, TeamPerformance,
                                        TechnicalReportCreate, TechnicalReportUpdate,
                                        TechnicalReportOut, ReportApproval, JobStatusResponse)
from src.repositories.technical_repositorie import TechnicalRepository
from src.repositories.booking_repositories import BookingRepository
from src.schemas.auth import Token  # Token model is reused
# Security/Auth Utilities
from src.service.auth import create_access_token  # JWT creation utility
from fastapi import Query
from datetime import date
from uuid import UUID
# --- Router Initialization ---
router = APIRouter(
    prefix="/technical",
    tags=["Technical Staff"],
)


# --- Dependency Injection for Controller ---
# ASSUMPTION: TechnicalController primarily depends on TechnicalRepository
def get_technical_controller(db: Session = Depends(get_db)) -> TechnicalController:
    tech_repo = TechnicalRepository(db)
    booking_repo = BookingRepository(db) # Instantiate BookingRepository
    # NOTE: If your controller needs other repos (e.g., TicketRepo), inject them here.
    return TechnicalController(db=db, tech_repo=tech_repo, booking_repo=booking_repo) # Pass booking_repo

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

@router.get("/worklist", summary="Technician Daily Jobs")
async def read_worklist(
    team_id: UUID, 
    target_date: date = Query(default=date.today()),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user) # Security check
):
    """Returns all jobs for the mechanic's specific team."""
    return await service.get_my_worklist(team_id, target_date)

@router.patch("/jobs/{booking_id}/status", response_model=JobStatusResponse, summary="Update Progress")
async def change_status(
    booking_id: int,
    status: str, # "IN_PROGRESS" or "COMPLETED"
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user)
):
    """Updates the car status and pings the customer automatically."""
    return await service.update_job_status(booking_id, status)

# --- PERFORMANCE ENDPOINTS ---

@router.get("/performance/me", response_model=TechnicalPerformance, summary="Get My Performance")
def get_my_performance(
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user)
):
    """Get performance metrics for the currently logged-in technical staff."""
    return service.get_technical_performance(current_user.technical_id, start_date, end_date)

@router.get("/performance/technical/{technical_id}", response_model=TechnicalPerformance, summary="Get Technical Staff Performance")
def get_technical_performance(
    technical_id: UUID,
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get performance metrics for a specific technical staff member. Admin or Technical only."""
    return service.get_technical_performance(technical_id, start_date, end_date)

@router.get("/performance/team/{team_id}", response_model=TeamPerformance, summary="Get Team Performance")
def get_team_performance(
    team_id: UUID,
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get performance metrics for a specific team. Admin or Technical only."""
    return service.get_team_performance(team_id, start_date, end_date)

@router.get("/performance/teams", response_model=List[TeamPerformance], summary="Get All Teams Performance")
def get_all_teams_performance(
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get performance metrics for all teams. Admin or Technical only."""
    return service.get_all_teams_performance(start_date, end_date)

@router.get("/performance/technicals", response_model=List[TechnicalPerformance], summary="Get All Technicals Performance")
def get_all_technicals_performance(
    start_date: date = Query(..., description="Start date for performance period"),
    end_date: date = Query(..., description="End date for performance period"),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get performance metrics for all technical staff. Admin or Technical only."""
    return service.get_all_technicals_performance(start_date, end_date)

# --- TECHNICAL REPORT ENDPOINTS ---

@router.post("/reports", response_model=TechnicalReportOut, status_code=201, summary="Submit Technical Report")
def create_report(
    report_in: TechnicalReportCreate,
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user)
):
    """Submit a technical report for a booking. Required before marking booking as COMPLETED."""
    return service.create_report(current_user.technical_id, report_in)

# --- ADMIN REPORT ENDPOINTS (must be before dynamic routes) ---

@router.get("/reports/admin/all", response_model=List[TechnicalReportOut], summary="Get All Reports (Admin)")
def get_all_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_admin_user)
):
    """Get all technical reports. Admin only."""
    return service.get_all_reports(skip, limit)

@router.get("/reports/admin/pending", response_model=List[TechnicalReportOut], summary="Get Pending Reports (Admin)")
def get_pending_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_admin_user)
):
    """Get all pending reports awaiting approval. Admin only."""
    return service.get_pending_reports(skip, limit)

# --- TECHNICAL REPORT ENDPOINTS (dynamic routes after static routes) ---

@router.get("/reports/me", response_model=List[TechnicalReportOut], summary="Get My Reports")
def get_my_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user)
):
    """Get all reports submitted by the current technical user."""
    return service.get_my_reports(current_user.technical_id, skip, limit)

@router.get("/reports/booking/{booking_id}", response_model=TechnicalReportOut, summary="Get Report by Booking")
def get_report_by_booking(
    booking_id: int,
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get the report for a specific booking. Admin or Technical only."""
    return service.get_report_by_booking(booking_id)

@router.get("/reports/{report_id}", response_model=TechnicalReportOut, summary="Get Report by ID")
def get_report(
    report_id: int,
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_user_admin_or_technical)
):
    """Get a specific report by ID. Admin or Technical only."""
    return service.get_report(report_id)

@router.put("/reports/{report_id}", response_model=TechnicalReportOut, summary="Update Technical Report")
def update_report(
    report_id: int,
    report_in: TechnicalReportUpdate,
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_technical_user)
):
    """Update a technical report. Only the author can update, and only before approval."""
    return service.update_report(report_id, current_user.technical_id, report_in)

@router.patch("/reports/{report_id}/approve", response_model=TechnicalReportOut, summary="Approve/Reject Report")
def approve_report(
    report_id: int,
    approval: ReportApproval,
    service: TechnicalController = Depends(get_technical_controller),
    current_user = Depends(get_current_admin_user)
):
    """Approve or reject a technical report. Admin only. Rejection requires feedback."""
    return service.approve_report(report_id, current_user.admin_id, approval)