from fastapi import HTTPException, status
from typing import List, Optional
from src.repositories.admin_repositories import AdminRepository
from src.repositories.technical_repositorie import TechnicalRepository
from src.models.admin_model import AdminLogin, AdminCreate, AdminUpdate
from src.schemas.admin import adminModel
from src.schemas.techincal import TechnicalModel
from src.models.technical_model import TechnicalCreate
from src.utils.hash_password import hash_password
from src.utils.verify_password import verify_password
from src.schemas.admin import adminModel
from uuid import UUID
class AdminController:
    """Handles the business logic for admin authentication and management."""

    def __init__(self, admin_repo: AdminRepository, tech_repo: TechnicalRepository):
        self.admin_repo = admin_repo
        self.tech_repo = tech_repo
        

    def authentication_admin(self, admin_in: AdminLogin) -> Optional[adminModel]:
        """Handle the admin login process."""
        admin = self.admin_repo.get_by_username(admin_in.username)
        if not admin:
            return None
        
        if not verify_password(admin_in.password, admin.password):
            return None
        
        return admin

    def get_admin_by_id(self, admin_id: UUID) -> adminModel:
        """Fetch a single admin, raising 404 if missing."""
        admin = self.admin_repo.get_by_id(admin_id)
        if not admin:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admin not found")
        return admin

    def create_admin(self, admin_in: AdminCreate) -> adminModel:
        """Handle creation of a new admin account."""
        # Check Username uniqueness
        if self.admin_repo.get_by_username(admin_in.username):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken.")

        # Check Contact uniqueness
        if self.admin_repo.get_by_email_phone(admin_in.email_phone):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email/Phone already in use.")

        hashed_password = hash_password(admin_in.password)
        return self.admin_repo.create(admin_in, hashed_password)

    def update_admin(self, admin_id: UUID, admin_in: AdminUpdate) -> adminModel:
        """Update admin details, rehashing password if changed."""
        admin = self.get_admin_by_id(admin_id) # Check existence

        # Logic to handle password hashing if it's being updated
        # (This requires your AdminUpdate model to handle Optional fields)
        update_data = admin_in.dict(exclude_unset=True)
        if "password" in update_data:
             update_data["password"] = hash_password(update_data["password"])

        return self.admin_repo.update(admin, update_data)

    def create_technical_account(self, tech_in: TechnicalCreate) -> TechnicalModel:
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
        return self.tech_repo.create(tech_in, hashed_password)