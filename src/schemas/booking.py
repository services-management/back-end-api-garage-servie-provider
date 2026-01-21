import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Text,Boolean, Enum as SQLEnum,BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Date, Time
from src.config.database import Base
from sqlalchemy import func
import uuid 

# 1. Define the Booking Statuses
class BookingStatus(str, enum.Enum):
    PENDING = "Pending"     # Initial state when user requests
    CONFIRMED = "Confirmed" # Admin has approved
    CANCELLED = "Cancelled" # User or Admin cancelled
    REJECTED = "Rejected"   # Admin denied the request
    COMPLETED = "Completed" # Service is finished
class BookingSource(str, enum.Enum):
    WEB = "Web"
    PHONE = "Phone"


class User(Base):
    __tablename__ = "users"

    # 1. Primary Identity
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 2. Contact Info (The 'Phone Number' is your lookup key)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # 3. Telegram Integration (Capture these when they start the bot)
    telegram_chat_id = Column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)
    
    # 4. Security State
    # nullable=True allows "Shadow Accounts" (No password yet)
    password_hash = Column(String(255), nullable=True) 
    
    # is_active=False means they are a guest who hasn't set a password/verified yet
    is_active = Column(Boolean, server_default='False', nullable=False)
    
    # 5. Metadata
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, onupdate=func.now())

    # 6. Relationships
    # This connects back to the Booking table we discussed earlier
    bookings = relationship("Booking", back_populates="customer")

class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("admin.admin_id"), nullable=True)
    technical_team_id = Column(UUID(as_uuid=True), ForeignKey("technical_team.team_id"), nullable=True)
    # NEW: Requirement - provide car details
    car_make = Column(String(50), nullable=False)   # e.g., "Toyota"
    car_model = Column(String(50), nullable=False)  # e.g., "Camry"

    # NEW: Requirement - share location and phone number
    service_location = Column(Text, nullable=False) # Address or Coordinates
    contact_phone = Column(String(20), nullable=False)
    note = Column(String(255),nullable=True)
    # Status & Source
    status = Column(
        SQLEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        nullable=False
    )
    source = Column(
        SQLEnum(BookingSource, name="booking_source"),
        nullable=False
    )
    
    # Schedule
    appointment_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    
    # 7. PAYMENT (essential)
    payment_status = Column(String, default="pending", nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=True)  # Calculated from services

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    customer = relationship("User", back_populates="bookings")
    items = relationship(
        "BookingItem",
        back_populates="booking",
        cascade="all, delete-orphan"
    )
    assigned_team = relationship("TechnicalTeam", backref="bookings")

class BookingItem(Base):
    """Stores the specific products/quantities used in a single booking."""
    __tablename__ = "booking_items"

    item_id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    # Capture the snapshot of data at the time of purchase
    quantity = Column(Numeric(10, 2), nullable=False)
    price_at_purchase = Column(Numeric(10, 2), nullable=False) 

    booking = relationship("Booking", back_populates="items")
    product = relationship("Product")
    service = relationship("Service")