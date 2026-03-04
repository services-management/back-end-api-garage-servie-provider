import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship,backref

from src.config.database import Base
from src.core.enums import BookingStatus, BookingSource, UserStatus


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

    # role field 
    role = Column(SQLEnum(UserStatus, name="user_status"))

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
    internal_note = Column(Text, nullable=True)
    assigned_garage_id = Column(UUID(as_uuid=True), nullable=True)
    technician_id = Column(UUID(as_uuid=True), nullable=True)
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
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=True)
    # Capture the snapshot of data at the time of purchase
    quantity = Column(Numeric(10, 2), nullable=False)
    price_at_purchase = Column(Numeric(10, 2), nullable=False) 

    booking = relationship("Booking", back_populates="items")
    product = relationship("Product")
    service = relationship("Service")


class BookingInvoice(Base):
    """Requirement: Get invoice from other source then upload after job completion"""
    __tablename__ = "booking_invoices"

    invoice_id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    # Stores the link to the invoice from the 'outside source'
    external_invoice_url = Column(String(500), nullable=False) 
    uploaded_at = Column(DateTime, server_default=func.now())
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("admin.admin_id"))
    booking = relationship("Booking", backref=backref("invoice", uselist=False))

class MaintenanceAlert(Base):
    """Requirement: Customer History and maintenance alerts"""
    __tablename__ = "maintenance_alerts"

    alert_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"))
    alert_date = Column(Date, nullable=False)
    message = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    user = relationship("User", backref="alerts")
    booking = relationship("Booking", backref="alerts")

class UserVehicle(Base):
    """Stores car details saved by a user in their profile."""
    __tablename__ = "user_vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    car_make = Column(String(50), nullable=False)
    car_model = Column(String(50), nullable=False)
    car_year = Column(Integer, nullable=True)
    car_engine = Column(String(50), nullable=True)
    license_plate = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", backref="saved_vehicles")