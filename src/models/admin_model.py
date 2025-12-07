from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.config.database import Base


class adminModel(Base):
    """SQLAlchemy User model for PostgreSQL database. Designed for Admin users."""
    __tablename__ = "Admin"
    
    # primary key (Used as the unique identifier in the JWT)
    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # login Credential (Must be unique for authentication)
    username = Column(String, unique=True, index=True, nullable=False)
    
    # Hashed password
    password = Column(String, nullable=False) 

    # Role Definition (Crucial for JWT claims and Authorization)
    role = Column(String, default="admin", nullable=False)
    
    # Contact Field (Fixed case sensitivity and added unique constraint)
    # The Python attribute is 'email_phone', but the DB column is explicitly 'Email_phone'
    email_phone = Column("Email_phone", String, unique=True, nullable=True)