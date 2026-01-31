import random
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.repositories.auth_repository import AuthRepository
from src.repositories.user_respositories import UserRepository
from src.service.auth import create_access_token
from src.config.telegram_client import telegram_client
from src.models.booking_model import VerifyOTP, LoginRequest
from src.schemas.auth import Token
from src.models.user_model import UserStatus

class OtpService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
        self.user_repo = UserRepository(db)

    async def request_otp(self, login_request: LoginRequest):
        phone = login_request.phone
        user = self.user_repo.get_user_by_phone(phone)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this phone number not found.")

        otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        self.auth_repo.create_otp(phone, otp_code)

        # Send OTP via Telegram
        if user.telegram_chat_id:
            message = f"Your OTP code is: {otp_code}"
            await telegram_client.send_message(user.telegram_chat_id, message)
        
        return {"message": "OTP sent successfully."}

    def verify_otp_and_login(self, verify_request: VerifyOTP) -> Token:
        phone = verify_request.phone
        otp_code = verify_request.otp_code

        otp = self.auth_repo.get_valid_otp(phone, otp_code)

        if not otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP.")

        self.auth_repo.mark_otp_as_used(otp)

        user = self.user_repo.get_user_by_phone(phone)
        if not user:
            # This should not happen if request_otp was called first, but as a safeguard
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if user.role == UserStatus.GUEST:
            self.user_repo.upgrade_shadow_to_active(user.user_id)
            print(f"User {user.user_id} upgraded from GUEST to CUSTOMER.")
        # Generate JWT token
        access_token = create_access_token(data={"sub": str(user.user_id), "role": "ACTIVE"}) # Assuming a 'customer' role
        return Token(access_token=access_token, token_type="bearer")
