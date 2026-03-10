from typing import List, Optional, Union
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.technical_model import (  # Assuming AdminUpdate exists
    TechnicalCreate, TechnicalUpdate)
from src.schemas.techincal import TechnicalModel
from src.schemas.techincal import TechnicalTeam  # Import your Team model
from src.models.technical_model import TechnicalTeamCreate, TechnicalTeamUpdate # Import schemas

class TechnicalRepository:
    """Implements the data access logic for the Technical entity."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique ID."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()

    def get_by_id(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Alias for get() to match common patterns."""
        return self.get(technical_id)

    def get_by_username(self, username: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique username."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.username == username).first()

    def get_by_phone_number(self, phone_number: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique phone number."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.phone_number == phone_number).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[TechnicalModel]:
        """Get multiple technical accounts with pagination."""
        return self.db.query(TechnicalModel).offset(skip).limit(limit).all()

    def create(self, tech_in: TechnicalCreate, hashed_password: str) -> TechnicalModel:
        """Creates a new Technical account."""
        try:
            db_tech = TechnicalModel(
                username=tech_in.username,
                password=hashed_password,
                phone_number=tech_in.phone_number,
                name=tech_in.name,
                role="technical",
                status="free",
                is_active=True
            )
            self.db.add(db_tech)
            self.db.commit()
            self.db.refresh(db_tech)
            return db_tech
        except IntegrityError as e:
            self.db.rollback()
            # Re-raise or handle the integrity error (e.g., duplicate key)
            raise e

    def update(self, db_obj: TechnicalModel, obj_in: Union[TechnicalUpdate, dict]) -> TechnicalModel:
        """Update an existing technical account record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Delete a technical account by ID."""
        obj = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
    
    def get_staff_by_name(self, name: str) -> List[TechnicalModel]:
        """Finds staff by name for human-friendly selection."""
        return self.db.query(TechnicalModel).filter(
            TechnicalModel.name.ilike(f"%{name}%")
        ).all()

    # --- TECHNICAL TEAM CRUD ---

    def get_team_by_name(self, team_name: str) -> Optional[TechnicalTeam]:
        """Finds an exact team by name (useful for direct assignment)."""
        return self.db.query(TechnicalTeam).filter(
            TechnicalTeam.team_name.ilike(team_name)
        ).first()

    def create_team(self, team_in: TechnicalTeamCreate) -> TechnicalTeam:
        """Creates a new technical team."""
        db_team = TechnicalTeam(
            team_name=team_in.team_name,
            description=team_in.description,
            team_lead_id=team_in.team_lead_id,
            is_active=True
        )
        try:
            self.db.add(db_team)
            self.db.commit()
            self.db.refresh(db_team)
            return db_team
        except IntegrityError as e:
            self.db.rollback()
            raise e

    def search_teams_by_name(self, name_substr: str) -> List[TechnicalTeam]:
        """Searches for teams with names containing the given substring."""
        return self.db.query(TechnicalTeam).filter(TechnicalTeam.team_name.ilike(f"%{name_substr}%")).all()

    def get_team(self, team_id: uuid.UUID) -> Optional[TechnicalTeam]:
        """Retrieves a team by its UUID."""
        # Note: Changed from .get(id) to a filter because team_id is a UUID
        return self.db.query(TechnicalTeam).filter(TechnicalTeam.team_id == team_id).first()

    def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[TechnicalTeam]:
        """Lists all teams with optional pagination."""
        return self.db.query(TechnicalTeam).offset(skip).limit(limit).all()

    def update_team(self, db_team: TechnicalTeam, obj_in: Union[TechnicalTeamUpdate, dict]) -> TechnicalTeam:
        """Updates team details like name, description, or team lead."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(db_team, key):
                setattr(db_team, key, value)

        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team

    def assign_member_to_team(self, technical_id: uuid.UUID, team_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Assigns a technical user to a specific team."""
        tech_user = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if tech_user:
            tech_user.team_id = team_id
            self.db.commit()
            self.db.refresh(tech_user)
        return tech_user
    
    def remove_member_from_team(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Removes a technical staff member from their current team."""
        tech_user = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if tech_user:
            tech_user.team_id = None  # Breaking the link
            self.db.commit()
            self.db.refresh(tech_user)
        return tech_user