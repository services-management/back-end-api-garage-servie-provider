from sqlalchemy.orm import Session
from typing import Optional
from src.models.technical_model import TechnicalModel # Assuming this is your new model
from src.schemas.technical_shema import TechnicalCreate # Assuming you create this schema
from src.utils.hash_password import hash_password # To hash the password before saving

class TechnicalRepository:
    """Implements the data access logic for the Technical entity."""

    def __init__(self, db: Session):
        # The database session is injected here
        self.db = db

    def get_by_username(self, username: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique username."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.username == username).first()

    def get_by_phone_number(self, phone_number: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique phone number."""
        # Note: This is necessary for checking for duplicates before creation (Business Logic)
        return self.db.query(TechnicalModel).filter(TechnicalModel.phone_number == phone_number).first()

    def create(self, tech_in: TechnicalCreate, hashed_password: str) -> TechnicalModel:
        """Creates a new Technical account with a pre-hashed password and default role."""

        db_tech = TechnicalModel(
            username=tech_in.username,
            password=hashed_password,
            phone_number=tech_in.phone_number,
            name=tech_in.name,
            # 'role' will use the default "technical" set in the model
            # 'status' will use the default "free" set in the model
        )

        self.db.add(db_tech)
        self.db.commit()
        self.db.refresh(db_tech)

        return db_tech