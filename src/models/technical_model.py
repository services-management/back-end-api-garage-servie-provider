from sqlalchemy import Column , String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID

import uuid
from src.config.database import Base

TechnicalStatusEnum = Enum("Free","Busy","off_duty", name = 'technical_status_enum')

class TechnicalModel(Base):
    '''sqlAlchemy model for Technical accounts'''
    __tablename__ = "Technical"
    # primary key
    technical_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,index=True)

    # Login Credentials (must be unique for authentication)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String,nullable=False)

    # contact
    phone_number = Column(String,unique=True,nullable=False)

    # identification
    name = Column(String,nullable=False)

    # Role
    role = Column(String,default="technical",nullable=False)

    # Operational Fields
    T_T_ID = Column(UUID(as_uuid=True), nullable=True) # Assuming the FK links to a Team ID
    status = Column(TechnicalStatusEnum, default="Free", nullable=False)