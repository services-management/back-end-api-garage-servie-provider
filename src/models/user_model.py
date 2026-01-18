from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime
import re

# User Schemas
class UserBase(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    telegram_chat_id: Optional[int] = None
    telegram_username: Optional[str] = Field(None, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

# Request Schemas
class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = False

class UserCreateWithPassword(UserBase):
    """Schema for creating user with required password"""
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user details"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    telegram_username: Optional[str] = Field(None, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            digits = re.sub(r'\D', '', v)
            if len(digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v

class UserProfileUpdate(UserUpdate):
    """Schema for updating user profile"""
    pass

class UserPasswordUpdate(BaseModel):
    """Schema for updating password"""
    current_password: Optional[str] = None
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserActivate(BaseModel):
    """Schema for activating a shadow account"""
    password: str = Field(..., min_length=8)
    confirm_password: str
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    phone: str = Field(..., min_length=10, max_length=20)
    password: str
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

class TelegramLink(BaseModel):
    """Schema for linking Telegram account"""
    telegram_chat_id: int
    telegram_username: Optional[str] = Field(None, max_length=100)

# Response Schemas
class UserResponse(UserBase):
    """Schema for user response"""
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserWithBookings(UserResponse):
    """User response with bookings"""
    bookings: List = []
    
    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """User statistics"""
    total_bookings: int = 0
    pending_bookings: int = 0
    completed_bookings: int = 0
    total_spent: float = 0.0

class UserDetailedResponse(UserResponse):
    """Detailed user response with stats"""
    stats: Optional[UserStats] = None

# Filter Schemas
class UserFilter(BaseModel):
    """Schema for filtering users"""
    phone: Optional[str] = None
    full_name: Optional[str] = None
    telegram_username: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    
    @validator('phone')
    def validate_phone_filter(cls, v):
        if v is not None:
            digits = re.sub(r'\D', '', v)
            if len(digits) < 3:
                raise ValueError('Phone search must have at least 3 digits')
        return v

# Token and Auth Schemas
class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[UUID] = None
    phone: Optional[str] = None

# Telegram Bot Schemas
class TelegramUserCreate(BaseModel):
    """Schema for creating user from Telegram"""
    telegram_chat_id: int
    telegram_username: Optional[str] = None
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v

# Admin Schemas
class UserBulkUpdate(BaseModel):
    """Schema for bulk updating users (admin)"""
    user_ids: List[UUID]
    is_active: Optional[bool] = None
    full_name: Optional[str] = None

class UserExportRequest(BaseModel):
    """Schema for user export request"""
    filters: Optional[UserFilter] = None
    format: str = Field("csv", regex="^(csv|json|excel)$")

# Validation Schemas
class PhoneValidation(BaseModel):
    """Schema for phone validation"""
    phone: str = Field(..., min_length=10, max_length=20)
    available: bool = True
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v