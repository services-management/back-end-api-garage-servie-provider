from typing import List, Optional
from uuid import UUID
import json

from fastapi import HTTPException, status
from datetime import date
from src.models.technical_model import (  # Added TechnicalUpdate
    TechnicalLogin, TechnicalStatusUpdate, TechnicalUpdate, TechnicalPerformance, TeamPerformance,
    TechnicalReportCreate, TechnicalReportUpdate, TechnicalReportOut, ReportApproval)
from src.repositories.technical_repositorie import TechnicalRepository, TechnicalReportRepository
from src.schemas.techincal import TechnicalModel  # Added TechnicalStatusUpdate
from src.schemas.booking import TechnicalReport
from src.utils.hash_password import hash_password  # Added for updates
from src.utils.verify_password import verify_password
from sqlalchemy.orm import Session
from src.repositories.booking_repositories import BookingRepository
from src.config.telegram_client import telegram_client

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

    async def _notify_admin_of_new_report(self, report, booking, technical_id):
        """
        Internal helper to send Telegram notification to admins when a new technical report is submitted.
        """
        from src.schemas.admin import adminModel
        from sqlalchemy import select
        
        # Get all active admins with telegram_chat_id
        admins = self.db.execute(
            select(adminModel).where(
                adminModel.is_active,
                adminModel.telegram_chat_id.isnot(None)
            )
        ).scalars().all()
        
        if not admins:
            print("⚠️ No active admins with Telegram found for report notification")
            return
        
        # Get technician name
        technician = self.tech_repo.get(technical_id)
        tech_name = technician.name if technician else "Unknown Technician"
        
        # Sanitize data to prevent injection attacks
        safe_car = f"{booking.car_make} {booking.car_model}"
        safe_date = booking.appointment_date.strftime("%Y-%m-%d") if booking.appointment_date else "TBD"
        safe_location = booking.service_location or "Garage"
        
        # Build notification message
        notification_msg = (
            f"📋 *NEW TECHNICAL REPORT SUBMITTED*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔧 *Technician:* {tech_name}\n"
            f"🚗 *Vehicle:* {safe_car}\n"
            f"📅 *Service Date:* {safe_date}\n"
            f"📍 *Location:* {safe_location}\n\n"
            f"📝 *Report Details:*\n"
            f"• Checklist items completed\n"
            f"• Parts used documented\n"
            f"• Photos/videos attached\n\n"
            f"👉 *Action Required:* Please review and approve/reject the report."
        )
        
        # Send to all admins with Telegram
        sent_count = 0
        for admin in admins:
            if admin.telegram_chat_id:
                try:
                    await telegram_client.send_message(
                        chat_id=admin.telegram_chat_id,
                        text=notification_msg,
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                    print(f"✅ Admin {admin.username} notified of new report for booking {booking.booking_id}")
                except Exception as e:
                    print(f"❌ Failed to notify admin {admin.username}: {e}")
        
        if sent_count == 0:
            print("⚠️ Report alert: No notifications were sent to admins")
        else:
            print(f"📢 Sent {sent_count} report alert(s) to admin(s)")

    async def _notify_technical_of_approval_decision(self, report, approval):
        """
        Internal helper to send Telegram notification to technical staff 
        when admin approves or rejects their report.
        """
        # Get the technician who submitted the report
        technician = self.tech_repo.get(report.technical_id)
        
        if not technician or not technician.telegram_chat_id:
            print("⚠️ Technician has no Telegram linked, skipping notification")
            return
        
        # Get booking info for context
        booking = self.booking_repo.get(report.booking_id)
        safe_car = f"{booking.car_make} {booking.car_model}" if booking else "Unknown Vehicle"
        
        # Build notification message based on approval/rejection
        if approval.is_approved:
            emoji = "✅"
            status_text = "APPROVED"
            action_text = "You can now mark this booking as COMPLETED."
            feedback_section = ""
        else:
            emoji = "❌"
            status_text = "REJECTED"
            action_text = "Please review the feedback and update your report."
            # Include admin feedback for rejections
            safe_feedback = self._sanitize_telegram_message(approval.admin_feedback or "No feedback provided")
            feedback_section = f"\n📝 *Admin Feedback:*\n{safe_feedback}"
        
        # Sanitize data to prevent injection attacks
        safe_date = booking.appointment_date.strftime("%Y-%m-%d") if booking and booking.appointment_date else "TBD"
        
        # Build notification message
        notification_msg = (
            f"{emoji} *REPORT {status_text}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚗 *Vehicle:* {safe_car}\n"
            f"📅 *Service Date:* {safe_date}\n\n"
            f"👉 *Action Required:* {action_text}"
            f"{feedback_section}\n\n"
            f"Check your dashboard for full details."
        )
        
        # Send notification
        try:
            await telegram_client.send_message(
                chat_id=technician.telegram_chat_id,
                text=notification_msg,
                parse_mode="Markdown"
            )
            tech_name = technician.name or technician.username
            result = "approved" if approval.is_approved else "rejected"
            print(f"✅ Technician {tech_name} notified that report was {result} for booking {booking.booking_id}")
        except Exception as e:
            print(f"❌ Failed to notify technician {technician.username}: {e}")

    async def update_job_status(self, booking_id: int, new_status: str, technical_user: TechnicalModel):
        """
        1. Updates status in DB
        2. Sends Telegram alert based on progress
        3. Validates booking belongs to user's team
        4. Requires approved report before marking as COMPLETED
        """
        # Check if trying to mark as COMPLETED - validate report first
        if new_status == "COMPLETED":
            if not self.report_repo.has_report(booking_id):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Cannot mark booking as COMPLETED. Please submit a technical report first."
                )
            # Check if report is approved
            report = self.report_repo.get_by_booking_id(booking_id)
            if not report.is_approved:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Cannot mark booking as COMPLETED. Technical report must be approved first."
                )

        # SECURITY: Fetch booking and verify it belongs to user's team
        booking = self.booking_repo.get(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found."
            )
        
        # SECURITY: Verify booking is assigned to user's team
        # Allow access if:
        # 1. User is a team member (team_id matches), OR
        # 2. User is the team lead of the team assigned to the booking
        
        is_team_member = technical_user.team_id and booking.technical_team_id and str(booking.technical_team_id) == str(technical_user.team_id)
        
        # Check if user is the team lead
        is_team_lead = False
        if not is_team_member and booking.technical_team_id:
            from src.schemas.techincal import TechnicalTeam
            team = self.db.query(TechnicalTeam).filter(TechnicalTeam.team_id == booking.technical_team_id).first()
            if team and team.team_lead_id and str(team.team_lead_id) == str(technical_user.technical_id):
                is_team_lead = True
        
        if not is_team_member and not is_team_lead:
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

        # Telegram Trigger for Status Updates
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

    async def create_report(self, technical_id: UUID, report_in: TechnicalReportCreate) -> TechnicalReportOut:
        """Create a new technical report for a booking."""
        # Verify the booking exists and is assigned to this technical's team
        booking = self.booking_repo.get(report_in.booking_id)
        if not booking:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Booking not found.")
        
        # SECURITY: Verify booking is assigned to user's team
        # Allow access if:
        # 1. User is a team member (team_id matches), OR
        # 2. User is the team lead of the team assigned to the booking
        
        # First, get the technical user to check their team membership/lead status
        tech_user = self.tech_repo.get(technical_id)
        if not tech_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Technical user not found.")
        
        is_team_member = tech_user.team_id and booking.technical_team_id and str(booking.technical_team_id) == str(tech_user.team_id)
        
        # Check if user is the team lead
        is_team_lead = False
        if not is_team_member and booking.technical_team_id:
            from src.schemas.techincal import TechnicalTeam
            team = self.db.query(TechnicalTeam).filter(TechnicalTeam.team_id == booking.technical_team_id).first()
            if team and team.team_lead_id and str(team.team_lead_id) == str(tech_user.technical_id):
                is_team_lead = True
        
        if not is_team_member and not is_team_lead:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only create reports for bookings assigned to your team."
            )
        
        # Create the report
        try:
            report = self.report_repo.create(report_in, technical_id)
            
            # Send notification to admin about new report submission
            try:
                await self._notify_admin_of_new_report(report, booking, technical_id)
            except Exception as e:
                # Log error but don't fail the report creation
                print(f"⚠️ Admin notification failed: {e}")
            
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

    async def approve_report(self, report_id: int, admin_id: UUID, approval: ReportApproval) -> TechnicalReportOut:
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
        
        # Send notification to technical staff about approval/rejection
        try:
            await self._notify_technical_of_approval_decision(updated_report, approval)
        except Exception as e:
            # Log error but don't fail the approval
            print(f"⚠️ Technical notification failed: {e}")
        
        return TechnicalReportOut(**self._parse_report(updated_report))
