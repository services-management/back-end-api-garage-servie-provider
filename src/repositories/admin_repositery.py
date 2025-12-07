
from sqlalchemy.orm import Session
from typing import Optional
from src.models.admin_model import adminModel
from src.utils import hash_password
from src.schemas.admin_shema import AdminCreate, AdminOut, AdminLogin
class AdminRepository:

    '''implement the data access logic for the admin entity'''
    def __init__(self,db:Session):
        # the database session is injected here
        self.db = db

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
    
    


