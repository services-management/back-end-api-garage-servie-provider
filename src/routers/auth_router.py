from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.controller.otp_controller import OtpService
from src.models.booking_model import LoginRequest, VerifyOTP
from src.schemas.auth import Token
from src.service.auth import refresh_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Schema for refresh token request
class RefreshTokenRequest(BaseModel):
    refresh_token: str

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

@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def refresh_token_endpoint(request: RefreshTokenRequest):
    """
    Refresh access token using a valid refresh token.
    
    Returns a new access token and refresh token pair.
    """
    try:
        # Get new access token from refresh token
        new_access_token = refresh_access_token(request.refresh_token)
        
        # Decode the refresh token to get user data for creating new refresh token
        from src.service.auth import decode_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
        payload = decode_token(request.refresh_token, token_type="refresh")
        
        # Create new refresh token (token rotation for security)
        payload.pop("exp", None)
        payload.pop("type", None)
        new_refresh_token = create_refresh_token(payload)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
