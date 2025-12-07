from pydantic import BaseModel, Field
import uuid
from typing import Optional

class TechnicalCreate(BaseModel):
    """Schema for creating a new Technical Account."""

    # login Credentials
    username: str = Field(min_length=4, max_length=50, description='Unique login identifier.')
    password: str = Field(min_length=8, description='Password must be hashed before storage.')

    name : str = Field(description="The technical staff's full name for display.")
    phone_number : str=Field(description="Unique phone number for contact/recovery.")

    class Config:
        from_attributes = True


class TechnicalOut(BaseModel):
    """Define the structure for safe Techincal output"""

    technical_id : uuid.UUID
    username: str
    name: str
    phone_number:str
    role:str
    status:str # enum
    T_T_ID:Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class TechincalLogin(BaseModel):
    """Define the input structure for a technical user to login request"""
    username:str
    password:str

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'