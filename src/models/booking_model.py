import enum
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID
from decimal import Decimal

# Define enums locally (don't import from models)
class BookingStatus(str, enum.Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    COMPLETED = "Completed"

class BookingSource(str, enum.Enum):
    WEB = "Web"
    PHONE = "Phone"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"
# --- Booking Service Schemas ---
class ProductSelection(BaseModel):
    product_id: int
    quantity: float
    price: Decimal

class BookingServiceBase(BaseModel):
    service_id: int

class BookingServiceResponse(BookingServiceBase):
    service_name: str
    products: List[ProductSelection] = []
    
    class Config:
        from_attributes = True

# --- Simplified Booking Schemas for Booking File Only ---
class BookingUserSimple(BaseModel):
    """Simple user schema for booking context only"""
    phone: str
    full_name: Optional[str] = None

class BookingCreate(BaseModel):
    # Customer Info (uses simplified schema)
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: Optional[str] = None
    
    # Car Info
    car_make: str = Field(..., max_length=50)
    car_model: str = Field(..., max_length=50)
    
    # Selection
    service_ids: List[int] = Field(..., min_items=1)
    appointment_date: date
    start_time: time
    
    # Meta
    service_location: str
    source: BookingSource = BookingSource.WEB
    note: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        digits = ''.join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v
    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        if v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

class BookingResponse(BaseModel):
    booking_id: int
    user_id: UUID
    contact_phone: str
    car_make: str
    car_model: str
    appointment_date: date
    start_time: time
    status: BookingStatus
    created_at: datetime
    services: List[BookingServiceResponse] = []
    
    class Config:
        from_attributes = True

# --- Additional Booking Schemas ---
class BookingUpdate(BaseModel):
    """Schema for updating booking"""
    status: Optional[BookingStatus] = None
    car_make: Optional[str] = None
    car_model: Optional[str] = None
    service_location: Optional[str] = None
    contact_phone: Optional[str] = None
    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    note: Optional[str] = None
    total_price: Optional[Decimal] = None
    payment_status: Optional[PaymentStatus] = None
    amount_paid: Optional[Decimal] = None
    technical_team_id: Optional[UUID] = None
    
    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        if v and v < date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v
    
class BookingPaymentUpdate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

# --- Team Assignment ---
class BookingTeamAssign(BaseModel):
    technical_team_id: UUID
    assigned_notes: Optional[str] = None
    
class BookingFilter(BaseModel):
    """Schema for filtering bookings"""
    user_id: Optional[UUID] = None
    status: Optional[BookingStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    car_make: Optional[str] = None
    source: Optional[BookingSource] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v