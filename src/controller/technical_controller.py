from typing import List, Optional
from uuid import UUID
import json

from fastapi import HTTPException, status
from datetime import date
from src.models.technical_model import (  # Added TechnicalUpdate
    TechnicalLogin, TechnicalStatusUpdate, TechnicalUpdate, TechnicalPerformance, TeamPerformance,
    TechnicalReportCreate, TechnicalReportUpdate, TechnicalReportOut, ReportApproval, JobStatusResponse)
from src.repositories.technical_repositorie import TechnicalRepository, TechnicalReportRepository
from src.schemas.techincal import TechnicalModel  # Added TechnicalStatusUpdate
from src.schemas.booking import TechnicalReport
from src.utils.hash_password import hash_password  # Added for updates
from src.utils.verify_password import verify_password
from sqlalchemy.orm import Session
from src.repositories.booking_repositories import BookingRepository
from src.config.telegram_client import telegram_client
from src.core.enums import BookingStatus

class TechnicalController:
    """Handles the business logic for technical user authentication and management."""

    def __init__(self, db:Session, tech_repo: TechnicalRepository, booking_repo: BookingRepository):
        self.db = db
        self.tech_repo = tech_repo
        self.booking_repo = booking_repo
        self.report_repo = TechnicalReportRepository(db)
        

    def authenticate_technical(self, tech_in: TechnicalLogin) -> Optional[TechnicalModel]:
        """Handles the technical user login process."""
        technical_user = self.tech_repo.get_by_username(tech_in.username)
        if not technical_user:
            return None
        
        if not verify_password(tech_in.password, technical_user.password):
            return None
        
        return technical_user

    def get_technical_by_id(self, tech_id: UUID) -> TechnicalModel:
        """Fetch a single technical user by ID, raising 404 if missing."""
        tech_user = self.tech_repo.get(tech_id)
        if not tech_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Technical account not found.")
        return tech_user

    def list_technical_users(self, skip: int = 0, limit: int = 100) -> List[TechnicalModel]:
        """Fetch multiple technical users with pagination (for admin access)."""
        return self.tech_repo.get_multi(skip=skip, limit=limit)

    def update_technical_user(self, tech_id: UUID, tech_in: TechnicalUpdate) -> TechnicalModel:
        """Update a technical user's details, rehashing the password if changed."""
        tech_user = self.get_technical_by_id(tech_id) 

        update_data = tech_in.model_dump(exclude_unset=True)
        
        # BUSINESS LOGIC: Hash password if it's in the update payload
        if "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])

        return self.tech_repo.update(tech_user, update_data)

    def update_technical_status(self, tech_id: UUID, status_in: TechnicalStatusUpdate) -> TechnicalModel:
        """Update only the assignment status of a technical user (Admin only operation)."""
    
        # 1. Fetch the existing user (this also handles the 404 check)
        tech_user = self.get_technical_by_id(tech_id)

        update_data = {"status":status_in}

        # 3. FIX: Use the Repository to update the data in the database
        # The Repository is responsible for database operations, not the model instance.
        return self.tech_repo.update(tech_user, update_data)

    def delete_technical_user(self, tech_id: UUID) -> None:
        """Delete a technical account by ID."""
        # Ensure the user exists before attempting to delete
        self.get_technical_by_id(tech_id) 
        self.tech_repo.remove(tech_id)

    # ----- booking related for technical users -----
    async def get_my_worklist(self, team_id: UUID, target_date: date):
        """Fetches assigned jobs for a specific team on a specific date."""
        # Ensure you use the repo function we built earlier: get_technical_jobs
        return self.booking_repo.get_technical_jobs(team_id, target_date)

    def _sanitize_telegram_message(self, text: str) -> str:
        """Sanitize text to prevent Telegram markdown injection."""
        if not text:
            return ""
        # Escape special Telegram markdown characters
        # Characters that need escaping in Telegram MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    async def update_job_status(self, booking_id: int, new_status: str, technical_user: TechnicalModel):
        """
        1. Updates status in DB
        2. Sends Telegram alert based on progress
        3. Validates booking belongs to user's team
        """
        # SECURITY: Fetch booking and verify it belongs to user's team
        booking = self.booking_repo.get(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found."
            )
        
        # SECURITY: Verify booking is assigned to user's team
        if not booking.technical_team_id or str(booking.technical_team_id) != str(technical_user.team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only update bookings assigned to your team."
            )
        
        # Update the booking status
        updated_booking = self.booking_repo.update_booking_status(booking_id, new_status)
        
        if not updated_booking:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking status."
            )

        # 2. Telegram Trigger for Status Updates
        if updated_booking.customer and updated_booking.customer.telegram_chat_id:
            # Define friendly messages based on the status
            if new_status == "IN_PROGRESS":
                status_text = "is now being worked on 🔧"
            elif new_status == "COMPLETED":
                status_text = "is READY for pickup! ✅"
            else:
                status_text = f"status has been updated to: {new_status}"

            # SECURITY: Sanitize car_make to prevent Telegram markdown injection
            safe_car_make = self._sanitize_telegram_message(updated_booking.car_make)
            msg = f"🚗 *Service Update:* Your {safe_car_make} {status_text}"
            await telegram_client.send_message(updated_booking.customer.telegram_chat_id, msg)
            
        return updated_booking
            msg = f"🚗 *Service Update:* Your {booking.car_make} {status_text}"
            await telegram_client.send_message(booking.customer.telegram_chat_id, msg)
        
        return JobStatusResponse(
            booking_id=booking.booking_id,
            status=booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
            message="Status updated successfully"
        )

    # ----- PERFORMANCE METRICS -----

    def get_technical_performance(self, technical_id: UUID, start_date: date, end_date: date) -> TechnicalPerformance:
        """Get performance metrics for a single technical staff member."""
        performance = self.tech_repo.get_technical_performance(technical_id, start_date, end_date)
        if not performance:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Technical account not found.")
        return performance

    def get_team_performance(self, team_id: UUID, start_date: date, end_date: date) -> TeamPerformance:
        """Get performance metrics for a technical team."""
        performance = self.tech_repo.get_team_performance(team_id, start_date, end_date)
        if not performance:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found.")
        return performance

    def get_all_teams_performance(self, start_date: date, end_date: date) -> List[TeamPerformance]:
        """Get performance metrics for all teams."""
        return self.tech_repo.get_all_teams_performance(start_date, end_date)

    def get_all_technicals_performance(self, start_date: date, end_date: date) -> List[TechnicalPerformance]:
        """Get performance metrics for all technical staff."""
        return self.tech_repo.get_all_technicals_performance(start_date, end_date)

    # ----- TECHNICAL REPORT METHODS -----

    def _parse_report(self, report: TechnicalReport) -> dict:
        """Parse report and convert JSON strings to objects."""
        # Parse vehicle info
        vehicle_info = None
        if report.vehicle_type or report.vin_number or report.fuel_type:
            vehicle_info = {
                "vehicle_type": report.vehicle_type,
                "vin_number": report.vin_number,
                "fuel_type": report.fuel_type,
                "fuel_quantity": report.fuel_quantity,
                "hybrid_type": report.hybrid_type
            }
        
        # Parse checklist items
        checklist_items = []
        if report.checklist_items:
            try:
                checklist_items = json.loads(report.checklist_items)
            except json.JSONDecodeError:
                checklist_items = []
        
        return {
            "report_id": report.report_id,
            "booking_id": report.booking_id,
            "technical_id": report.technical_id,
            # Vehicle Info
            "vehicle_info": vehicle_info,
            # Checklist
            "checklist_items": checklist_items,
            # Work Description
            "work_description": report.work_description,
            "parts_used": report.parts_used,
            "additional_notes": report.additional_notes,
            # Media
            "image_urls": json.loads(report.image_urls) if report.image_urls else [],
            "video_urls": json.loads(report.video_urls) if report.video_urls else [],
            # Approval
            "is_approved": report.is_approved,
            "approved_by": report.approved_by,
            "approved_at": report.approved_at,
            "admin_feedback": report.admin_feedback,
            # Timestamps
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }

    def create_report(self, technical_id: UUID, report_in: TechnicalReportCreate) -> TechnicalReportOut:
        """Create a new technical report for a booking."""
        # Verify the booking exists and is assigned to this technical's team
        booking = self.booking_repo.get(report_in.booking_id)
        if not booking:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Booking not found.")
        
        # Create the report
        try:
            report = self.report_repo.create(report_in, technical_id)
            return TechnicalReportOut(**self._parse_report(report))
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    def update_report(self, report_id: int, technical_id: UUID, report_in: TechnicalReportUpdate) -> TechnicalReportOut:
        """Update an existing report. Only the author can update."""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found.")
        
        # Verify ownership
        if report.technical_id != technical_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You can only update your own reports.")
        
        # Cannot update approved reports
        if report.is_approved:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot update an approved report.")
        
        updated_report = self.report_repo.update(report_id, report_in)
        return TechnicalReportOut(**self._parse_report(updated_report))

    def get_report(self, report_id: int) -> TechnicalReportOut:
        """Get a report by ID."""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found.")
        return TechnicalReportOut(**self._parse_report(report))

    def get_report_by_booking(self, booking_id: int) -> TechnicalReportOut:
        """Get report for a specific booking."""
        report = self.report_repo.get_by_booking_id(booking_id)
        if not report:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No report found for this booking.")
        return TechnicalReportOut(**self._parse_report(report))

    def get_my_reports(self, technical_id: UUID, skip: int = 0, limit: int = 100) -> List[TechnicalReportOut]:
        """Get all reports by a technical user."""
        reports = self.report_repo.get_reports_by_technical(technical_id, skip, limit)
        return [TechnicalReportOut(**self._parse_report(r)) for r in reports]

    def get_pending_reports(self, skip: int = 0, limit: int = 100) -> List[TechnicalReportOut]:
        """Get all pending reports (for admin)."""
        reports = self.report_repo.get_pending_reports(skip, limit)
        return [TechnicalReportOut(**self._parse_report(r)) for r in reports]

    def get_all_reports(self, skip: int = 0, limit: int = 100) -> List[TechnicalReportOut]:
        """Get all reports (for admin)."""
        reports = self.report_repo.get_all_reports(skip, limit)
        return [TechnicalReportOut(**self._parse_report(r)) for r in reports]

    def approve_report(self, report_id: int, admin_id: UUID, approval: ReportApproval) -> TechnicalReportOut:
        """Approve or reject a report (admin only)."""
        report = self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found.")
        
        # If rejecting, feedback is required
        if not approval.is_approved and not approval.admin_feedback:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Admin feedback is required when rejecting a report."
            )
        
        updated_report = self.report_repo.approve(
            report_id, admin_id, approval.is_approved, approval.admin_feedback
        )
        return TechnicalReportOut(**self._parse_report(updated_report))
