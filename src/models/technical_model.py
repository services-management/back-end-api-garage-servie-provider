from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
import re
import uuid

# --- Status Enum/Literal (Important for validation) ---
# Assuming these are the allowed statuses for a Technical user
TechnicalStatus = Literal['free', 'busy', 'off_duty']

# --- Input Schemas ---

class TechnicalCreate(BaseModel):
    """Schema for creating a new Technical Account."""
    username: str = Field(min_length=4, max_length=50, description='Unique login identifier.')
    password: str = Field(min_length=8, description='Password must be hashed before storage.')
    name : str = Field(description="The technical staff's full name for display.")
    phone_number : str = Field(description="Unique phone number for contact/recovery.")

    @validator('phone_number')
    def validate_phone(cls, v):
        # Simple check: Ensure it looks like a phone number (digits and optional plus sign)
        phone_regex = r'^\+?[0-9]{7,15}$'
        if not re.match(phone_regex, v):
            raise ValueError('Must be a valid phone number (digits only, optional + at start)')
        return v

    class Config:
        from_attributes = True

class TechnicalLogin(BaseModel):
    """Define the input structure for a technical user to login request."""
    username: str
    password: str

class TechnicalUpdate(BaseModel):
    """Schema for updating Technical account details (partial update)."""
    username: Optional[str] = Field(None, min_length=4, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    name: Optional[str] = None
    phone_number: Optional[str] = None
    # Note: Status and Role are usually updated separately by an Admin, 
    # but we include status here for flexibility.
    status: Optional[TechnicalStatus] = None 
    
    @validator('phone_number', pre=True, always=True)
    def validate_phone_on_update(cls, v):
        if v is not None:
            phone_regex = r'^\+?[0-9]{7,15}$'
            if not re.match(phone_regex, v):
                raise ValueError('Must be a valid phone number (digits only, optional + at start)')
        return v

# Dedicated schema for admin to change status
class TechnicalStatusUpdate(BaseModel):
    """Schema for an Admin to update only the status of a Technical account."""
    status: TechnicalStatus

# --- Output Schemas ---

class TechnicalOut(BaseModel):
    """Define the structure for safe Technical output (excluding password)."""
    # 💡 FIX: Changed from uuid.UUID to int for repository consistency
    technical_id: uuid.UUID
    username: str
    name: str
    phone_number: str
    role: str
    status: TechnicalStatus # Use the Literal type for better validation
    T_T_ID: Optional[int] = None # Assuming Trouble Ticket ID is an int/UUID

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Defines the structure of the authentication token returned to the client."""
    access_token: str
    token_type: str = 'bearer'