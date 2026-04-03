import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from src.core.enums import ServiceType

from pydantic import BaseModel, Field, validator, model_validator, computed_field


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

class BookingItemCreate(BaseModel):
    
    service_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: float
    @model_validator(mode='after')
    def validate_item_selection(self):
        if not self.service_id and not self.product_id:
            raise ValueError("Item must have either a service_id or a product_id")
        return self
    
# --- Booking Service Schemas ---
class BookingCreate(BaseModel):
    # Customer Identity
    contact_phone: str = Field(...,alias="phone", example="+1234567890")
    full_name: Optional[str] = None
    
    # Car Requirements
    vehicle_id: Optional[int] = Field(None, example=1)
    car_make: str = Field(..., example="Toyota")
    car_model: str = Field(..., example="Camry")
    car_year: Optional[int] = Field(None, example=2023)
    car_engine: Optional[str] = Field(None, example="2.5L Hybrid")
    
    items: List[BookingItemCreate] = Field(..., min_length=1)
    # Logistics
    appointment_date: date
    start_time: time
    service_location: str # Can be address or GPS string
    note: Optional[str] = None
    source: BookingSource = Field(example= BookingSource.WEB)
    service_mode: ServiceType = Field(default=ServiceType.GARAGE)
    @validator('appointment_date')
    def date_must_be_future(cls, v):
        if v < date.today():
            raise ValueError('Date must be today or in the future')
        return v
    
class BookingItemResponse(BaseModel):
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: float
    unit_price: Decimal = Field(alias="price_at_purchase")

    @model_validator(mode='before')
    @classmethod
    def resolve_names(cls, data):
        # Extract names from relationships if they exist
        service_obj = getattr(data, 'service', None)
        product_obj = getattr(data, 'product', None)

        if service_obj:
            setattr(data, 'service_name', service_obj.name)
        if product_obj:
            setattr(data, 'product_name', product_obj.name)
            
        return data
    @computed_field
    @property
    def subtotal(self) -> Decimal:
        # 2. Calculate Subtotal automatically whenever the object is serialized
        return self.unit_price * Decimal(str(self.quantity))

    class Config:
        from_attributes = True
        populate_by_name = True

class InvoiceResponse(BaseModel):
    external_invoice_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Simple schema for customer info in booking responses
class CustomerInfoForBooking(BaseModel):
    full_name: str
    phone: str
    
    class Config:
        from_attributes = True

class BookingHistoryResponse(BaseModel):
    booking_id: int
    vehicle_id: Optional[int]
    car_make: str
    car_model: str
    car_year: Optional[int]
    car_engine: Optional[str]
    appointment_date: date
    start_time: time
    status: str # e.g., "Pending", "Completed"
    service_location: str
    total_price: Optional[Decimal]
    status: BookingStatus
    items: List[BookingItemResponse] 
    # This is where our 'backref' relationship pays off!
    # If no invoice exists yet, this will simply be null
    invoice: Optional[InvoiceResponse] = None
    
    # Customer information (nested from customer relationship)
    customer: Optional[CustomerInfoForBooking] = None
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str

class VerifyOTP(BaseModel):
    phone: str
    otp_code: str = Field(..., min_length=6, max_length=6)

class AdminBookingCreate(BookingCreate):
    assigned_garage_id: UUID
    source: BookingSource = Field(example= BookingSource.PHONE)
    internal_note: Optional[str] = Field(None, example="Customer is in a hurry.")
    
class BookingSuccessResponse(BaseModel):
    booking: BookingHistoryResponse  # Your existing booking data
    telegram_link: str | None             # The Magic Link for the shadow user