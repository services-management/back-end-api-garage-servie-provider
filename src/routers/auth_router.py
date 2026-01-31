from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.controller.otp_controller import OtpService
from src.models.booking_model import LoginRequest, VerifyOTP
from src.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_otp_service(db: Session = Depends(get_db)):
    return OtpService(db)

@router.post("/otp/request", status_code=status.HTTP_200_OK)
async def request_otp(
    login_request: LoginRequest, 
    service: OtpService = Depends(get_otp_service)
):
    """
    Requests an OTP for a given phone number.
    """
    return await service.request_otp(login_request)

@router.post("/otp/verify", response_model=Token, status_code=status.HTTP_200_OK)
def verify_otp_and_login(
    verify_request: VerifyOTP, 
    service: OtpService = Depends(get_otp_service)
):
    """
    Verifies the OTP and returns a JWT token upon success.
    """
    return service.verify_otp_and_login(verify_request)
