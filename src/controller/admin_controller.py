from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from src.config.settings import settings
from src.models.admin_model import AdminCreate, AdminLogin, AdminUpdate, AdminOut
from src.models.technical_model import TechnicalCreate, TechnicalOut
from src.repositories.admin_repositories import AdminRepository
from src.repositories.technical_repositorie import TechnicalRepository
from src.schemas.admin import adminModel
from src.schemas.techincal import TechnicalModel, TechnicalTeam
from src.utils.hash_password import hash_password
from src.utils.verify_password import verify_password
from src.config.telegram_client import telegram_client
from src.models.booking_model import AdminBookingCreate, BookingStatus
from src.repositories.booking_repositories import BookingRepository
from src.models.technical_model import TechnicalTeamCreate
class AdminController:
    """Handles the business logic for admin authentication and management."""

    def __init__(self, db:Session, admin_repo: AdminRepository, tech_repo: TechnicalRepository, booking_repo: BookingRepository):
        self.db = db
        self.admin_repo = admin_repo
        self.tech_repo = tech_repo
        self.booking_repo = booking_repo
        

    def authentication_admin(self, admin_in: AdminLogin) -> Optional[adminModel]:
        """Handle the admin login process."""
        admin = self.admin_repo.get_by_username(admin_in.username)
        if not admin:
            return None
        
        if not verify_password(admin_in.password, admin.password):
            return None
        
        if not admin.is_active:
             raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

        return admin

    def get_admin_by_id(self, admin_id: UUID) -> adminModel:
        """Fetch a single admin, raising 404 if missing."""
        admin = self.admin_repo.get_by_id(admin_id)
        if not admin:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admin not found")
        return admin

    def get_all_admins(self, skip: int = 0, limit: int = 100) -> list[adminModel]:
        """Fetch all admin accounts."""
        return self.admin_repo.get_multi(skip=skip, limit=limit)

    def get_all_technicals(self, skip: int = 0, limit: int = 100) -> list[TechnicalModel]:
        """Fetch all technical accounts."""
        return self.tech_repo.get_multi(skip=skip, limit=limit)

    def deactivate_admin(self, admin_id: UUID) -> adminModel:
        """Deactivate an admin account."""
        admin = self.get_admin_by_id(admin_id)
        return self.admin_repo.update(admin, {"is_active": False})

    def deactivate_technical(self, technical_id: UUID) -> TechnicalModel:
        """Deactivate a technical account."""
        tech = self.tech_repo.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if not tech:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Technical account not found")
        return self.tech_repo.update(tech, {"is_active": False})

    def _generate_magic_link(self, user_id: UUID, role: str) -> str:
        """Generates a Telegram deep link for account linking."""
        bot_username = settings.TELEGRAM_BOT_USERNAME
        # Format: https://t.me/bot?start=ROLE_UUID
        return f"https://t.me/{bot_username}?start={role}_{user_id}"

    def get_admin_magic_link(self, admin_id: UUID) -> dict:
        """Get the Telegram magic link for an existing admin."""
        admin = self.get_admin_by_id(admin_id)
        magic_link = self._generate_magic_link(admin.admin_id, "admin")
        return {
            "admin_id": str(admin.admin_id),
            "username": admin.username,
            "telegram_magic_link": magic_link,
            "telegram_chat_id": admin.telegram_chat_id
        }

    def get_technical_magic_link(self, technical_id: UUID) -> dict:
        """Get the Telegram magic link for an existing technical."""
        tech = self.tech_repo.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if not tech:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Technical account not found")
        magic_link = self._generate_magic_link(tech.technical_id, "tech")
        return {
            "technical_id": str(tech.technical_id),
            "username": tech.username,
            "telegram_magic_link": magic_link,
            "telegram_chat_id": tech.telegram_chat_id
        }

    def create_admin(self, admin_in: AdminCreate) -> AdminOut:
        """Handle creation of a new admin account."""
        # Check Username uniqueness
        if self.admin_repo.get_by_username(admin_in.username):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken.")

        # Check Contact uniqueness
        if self.admin_repo.get_by_email_phone(admin_in.email_phone):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email/Phone already in use.")

        hashed_password = hash_password(admin_in.password)
        db_admin = self.admin_repo.create(admin_in, hashed_password)
        
        # Convert to Pydantic and add link
        out = AdminOut.from_orm(db_admin)
        out.telegram_magic_link = self._generate_magic_link(db_admin.admin_id, "admin")
        return out

    def update_admin(self, admin_id: UUID, admin_in: AdminUpdate) -> adminModel:
        """Update admin details, rehashing password if changed."""
        admin = self.get_admin_by_id(admin_id) # Check existence

        # Logic to handle password hashing if it's being updated
        # (This requires your AdminUpdate model to handle Optional fields)
        update_data = admin_in.dict(exclude_unset=True)
        if "password" in update_data:
             update_data["password"] = hash_password(update_data["password"])

        return self.admin_repo.update(admin, update_data)

    def create_technical_account(self, tech_in: TechnicalCreate) -> TechnicalOut:
        """Create a technical account with cross-table conflict checks."""
        # Check Username across both tables
        if self.admin_repo.get_by_username(tech_in.username) or self.tech_repo.get_by_username(tech_in.username):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username taken.")

        # Check Phone across Technical table
        if self.tech_repo.get_by_phone_number(tech_in.phone_number):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Phone number linked to another Technical account.")
        
        # Check Phone across Admin table (Bug fix applied here)
        if self.admin_repo.get_by_email_phone(tech_in.phone_number):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Phone number linked to an Admin account.")

        hashed_password = hash_password(tech_in.password)
        db_tech = self.tech_repo.create(tech_in, hashed_password)
        
        # Convert to Pydantic and add link
        out = TechnicalOut.from_orm(db_tech)
        out.telegram_magic_link = self._generate_magic_link(db_tech.technical_id, "tech")
        return out
    
    # ---- Booking Management for Admins ----

    async def accept_booking(self, booking_id: int):
        booking = self.booking_repo.update_booking_status(booking_id, BookingStatus.CONFIRMED)
        if booking and booking.customer and booking.customer.telegram_chat_id:
            msg = (
                f"✅ *Booking Accepted!*\n"
                f"Your appointment for the {booking.car_make} is confirmed.\n"
                f"📅 Date: {booking.appointment_date}\n"
                f"⏰ Time: {booking.start_time}"
            )
            await telegram_client.send_message(booking.customer.telegram_chat_id, msg)
        return booking
    
    async def reject_booking(self, booking_id: int, reason: str):
        """
        Moves booking to CANCELLED and notifies the user why.
        """
        # We use your repo's cancel_booking logic
        success = self.booking_repo.cancel_booking(booking_id)
        booking = self.booking_repo.get_with_items(booking_id)
        # reason = input("Please provide a reason for rejection: ")
        if success and booking.customer and booking.customer.telegram_chat_id:
            msg = (
                f"❌ *Booking Update*\n"
                f"Regrettably, we cannot fulfill your booking #{booking_id}.\n"
                f"Reason: {reason}\n"
                f"Please contact us to reschedule."
            )
            await telegram_client.send_message(booking.customer.telegram_chat_id, msg)
        return booking

    async def create_booking_for_customer(self, booking_info: AdminBookingCreate):
        """
        1. Admin-specific booking creation logic.
        2. Directly assign to a garage or technician.
        3. Bypass certain validations if needed.
        """
        # check user have account or not 
        user = self.booking_repo.user_repo.get_user_by_phone(booking_info.contact_phone)
        if not user:
            # create shadow account 
            user = self.booking_repo.user_repo.create_shadow_account(
                phone=booking_info.contact_phone,
                full_name=booking_info.full_name
            )   
        
        # We don't modify the booking_info object if it's strictly validated by Pydantic
        # Instead, we pass user.user_id to the repo method
        booking = self.booking_repo.create_admin_booking(booking_info, user.user_id)
        
        # Technician check
        if not booking.technician_id:
             # If it wasn't provided in booking_info, this might fail depending on requirements.
             # The router/schema might already enforce this.
             pass

        if booking.customer and booking.customer.telegram_chat_id:
           message = (
            f"✅ *New Appointment Scheduled*\n\n"
            f"The garage has scheduled a service for your {booking.car_make}.\n"
            f"📅 *Date:* {booking.appointment_date}\n"
            f"⏰ *Time:* {booking.start_time}\n"
            f"📍 *Location:* {booking.service_location}"
        )
           await telegram_client.send_message(booking.customer.telegram_chat_id, message)

        return booking
    
    async def get_daily_overview(self, target_date: date):
        """
        Improved: Returns today's stats and all relevant activity.
        1. Stats for the specific day.
        2. All bookings that are PENDING (action required) or scheduled for that day.
        """
        from sqlalchemy import or_
        from src.schemas.booking import Booking, BookingStatus
        
        # 1. Stats specifically for target_date
        stats = self.booking_repo.get_booking_counts_by_status(target_date)
        
        # 2. Activity: Show everything scheduled for today OR anything that is still PENDING/REJECTED/REJECTED
        # basically anything that needs admin attention today.
        bookings = self.db.query(Booking).filter(
            or_(
                Booking.appointment_date == target_date,
                Booking.status == BookingStatus.PENDING
            )
        ).options(
            joinedload(Booking.customer)
        ).order_by(Booking.status, Booking.start_time).all()

        return {
            "stats": stats,
            "bookings": bookings
        }
    
    # Inside your AdminController class
    async def get_all_bookings_filtered(self, query: str = None, status: str = None, limit: int = 100):
        """
        Business logic to fetch filtered bookings. 
        You can add extra logic here, like audit logging who performed the search.
        """
        return self.booking_repo.search_bookings(query=query, status=status, limit=limit)
    
    async def assign_team(self, booking_id: int, technical_team_id: UUID):
        """Assign a technical team to a booking by its UUID."""
        # Check if team exists
        team = self.db.query(TechnicalTeam).filter(TechnicalTeam.team_id == technical_team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail=f"Team with ID '{technical_team_id}' not found.")
        
        booking = self.booking_repo.assign_technical_team(booking_id, team.team_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found.")
            
        return booking
    
    # -- technical team management by admin --

    async def create_new_team(self, team_data: TechnicalTeamCreate):
        """Logic to create a team and optionally assign an initial lead."""
        return self.tech_repo.create_team(team_data)

    async def list_all_teams(self, skip: int = 0, limit: int = 100):
        """Returns all teams for the admin dashboard."""
        return self.tech_repo.get_all_teams(skip=skip, limit=limit)

    async def get_team_details(self, team_name: str):
        """Fetches a specific team's details."""
        teams = self.tech_repo.search_teams_by_name(team_name)
        if not teams:
            raise ValueError("Team not found")  
        
        return teams[0]

    async def add_staff_to_team_friendly(self, staff_name: str, team_name: str):
        """Allows Admin to type 'Add John Doe to Team Alpha'."""
        # 1. Resolve Human Names to UUIDs
        staff_id = await self._resolve_staff_id_by_name(staff_name)
        
        teams = self.tech_repo.search_teams_by_name(team_name)
        if not teams:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")
        team_id = teams[0].team_id
        
        # 2. Execute the actual assignment
        return await self.add_staff_to_team(staff_id, team_id)
    
    async def remove_staff_from_team_friendly(self, staff_name: str):
        """Allows Admin to type 'Remove John Doe'."""
        staff_id = await self._resolve_staff_id_by_name(staff_name)
        return await self.remove_staff_from_team(staff_id)
    

    # helper functions can be added here as needed
    async def _resolve_staff_id_by_name(self, name: str) -> UUID:
        """Internal helper to find a technical staff UUID by their name."""
        results = self.tech_repo.get_staff_by_name(name) # Requires this in repo
        if not results:
            raise HTTPException(status_code=404, detail=f"No staff found with name '{name}'")
        if len(results) > 1:
            # Prevent 'The Double John' problem
            details = ", ".join([f"{u.name} ({u.phone_number})" for u in results])
            raise HTTPException(
                status_code=400, 
                detail=f"Multiple results for '{name}'. Please be more specific: {details}"
            )
        return results[0].technical_id
    
