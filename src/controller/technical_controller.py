from src.repositories.technical_repositorie import TechnicalRepository
from src.models.technical_model import TechnicalUpdate,TechnicalStatusUpdate,TechnicalLogin # Added TechnicalUpdate
from src.utils.verify_password import verify_password
from src.utils.hash_password import hash_password # Added for updates
from src.schemas.techincal import TechnicalModel# Added TechnicalStatusUpdate
from fastapi import HTTPException, status
from typing import Optional, List, Union
from sqlalchemy.orm import Session
from uuid import UUID
class TechnicalController:
    """Handles the business logic for technical user authentication and management."""

    def __init__(self, tech_repo: TechnicalRepository):
        self.tech_repo = tech_repo
        

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

        update_data = tech_in.dict(exclude_unset=True)
        
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