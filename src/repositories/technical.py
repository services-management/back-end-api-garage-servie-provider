from sqlalchemy.orm import Session
from typing import Optional, List, Union
from sqlalchemy.exc import IntegrityError
from src.schemas.techincal import TechnicalModel
from src.models.technical import TechnicalCreate, TechnicalUpdate # Assuming AdminUpdate exists
from src.utils.hash_password import hash_password 

class TechnicalRepository:
    """Implements the data access logic for the Technical entity."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique ID."""
        return self.db.query(TechnicalModel).get(id)

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
                # Role and status defaults are assumed to be handled by the model
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

    def remove(self, id: int) -> Optional[TechnicalModel]:
        """Delete a technical account by ID."""
        obj = self.db.query(TechnicalModel).get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj