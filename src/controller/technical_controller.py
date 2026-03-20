from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from datetime import date
from src.models.technical_model import (  # Added TechnicalUpdate
    TechnicalLogin, TechnicalStatusUpdate, TechnicalUpdate)
from src.repositories.technical_repositorie import TechnicalRepository
from src.schemas.techincal import TechnicalModel  # Added TechnicalStatusUpdate
from src.utils.hash_password import hash_password  # Added for updates
from src.utils.verify_password import verify_password
from sqlalchemy.orm import Session
from src.repositories.booking_repositories import BookingRepository
from src.config.telegram_client import telegram_client

class TechnicalController:
    """Handles the business logic for technical user authentication and management."""

    def __init__(self, db:Session,tech_repo: TechnicalRepository, booking_repo: BookingRepository):
        self.db = db
        self.tech_repo = tech_repo
        self.booking_repo = booking_repo
        

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