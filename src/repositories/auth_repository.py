from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from src.schemas.otp import OTP

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_otp(self, phone: str, otp_code: str) -> OTP:
        otp = OTP(phone=phone, otp_code=otp_code)
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp

    def get_valid_otp(self, phone: str, otp_code: str) -> Optional[OTP]:
        return self.db.query(OTP).filter(
            OTP.phone == phone,
            OTP.otp_code == otp_code,
            OTP.is_used.is_(False),  # Only return unused OTPs
            OTP.expires_at > datetime.utcnow()
        ).first()

    def mark_otp_as_used(self, otp: OTP):
        otp.is_used = True
        self.db.commit()
