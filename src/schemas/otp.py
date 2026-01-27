import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from src.config.database import Base

class OTP(Base):
    __tablename__ = "otps"

    otp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    def __init__(self, phone: str, otp_code: str, expires_in_minutes: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.phone = phone
        self.otp_code = otp_code
        self.expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
