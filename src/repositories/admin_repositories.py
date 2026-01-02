
from sqlalchemy.orm import Session
from typing import Optional
from src.schemas.admin import adminModel
from src.models.admin_model import AdminCreate
from src.utils.hash_password import hash_password
import uuid

class AdminRepository:
    '''implement the data access logic for the admin entity'''
    def __init__(self, db: Session):
        # the database session is injected here
        self.db = db

    def create_default_admin(self, username: str, password: str, email_phone: str) -> adminModel:
        """
        Creates a new Admin user with a hashed password.
        This is often called by a startup script or test setup.
        """
        # 1. Check if the user already exists to prevent duplicates
        if self.db.query(adminModel).filter(adminModel.username == username).first():
             # If you want to silently skip creation, just return None
            return None 

        # 2. Hash the password
        hashed_password = hash_password(password)
        
        # 3. Create the Admin model instance
        db_admin = adminModel(
            username=username,
            password=hashed_password,
            email_phone=email_phone,
            role="admin", # Assuming a default role
        )
        
        # 4. Add and commit to the database
        self.db.add(db_admin)
        self.db.commit()
        self.db.refresh(db_admin)
        return db_admin
    def get_by_id(self,id:uuid.UUID) -> adminModel | None:
        """Retrieve an admin account by matching id field"""
        return self.db.query(adminModel).filter(adminModel.admin_id==id).first()
    def get_by_username(self, username:str ) -> adminModel | None:
        """Get all users from the database."""
        return self.db.query(adminModel).filter(adminModel.username == username).first()

    def get_by_email_phone(self, contact_info: str) -> Optional[adminModel]:
        """Retrieves an Admin account by matching the email_phone field."""
        # Use the explicit column name "Email_phone" if needed due to PostgreSQL case sensitivity
        return self.db.query(adminModel).filter(adminModel.email_phone == contact_info).first()

    def create(self, username: AdminCreate, hashed_password:str ) -> adminModel:
        """Create a new user with hashed password."""
        db_admin = adminModel(
            username=username.username,
            password=hashed_password,
            email_phone= username.email_phone,
            role="admin"
        )
        self.db.add(db_admin)
        self.db.commit()
        self.db.refresh(db_admin)
        return db_admin
    
    def update(self, db_obj: adminModel, update_data: dict | AdminCreate) -> adminModel:
        """
        Update an existing admin record.
        """
        # Convert Pydantic model to dict if necessary
        if not isinstance(update_data, dict):
            update_data = update_data.dict(exclude_unset=True)

        # Update model attributes
        for key, value in update_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    