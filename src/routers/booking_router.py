from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.controller.booking_controller import BookingService
from src.dependency.auth import get_current_customer
from src.models.user_model import UserResponse
from src.models.booking_model import BookingCreate, BookingHistoryResponse, BookingSuccessResponse


router = APIRouter(prefix="/bookings", tags=["Bookings"])

# Dependency to initialize the service
def get_booking_service(db: Session = Depends(get_db)):
    return BookingService(db)

@router.post("/", response_model=BookingSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_new_booking(
    booking_data: BookingCreate, 
    service: BookingService = Depends(get_booking_service)
):
    """
    Endpoint for Guest Bookings.
    It creates a Shadow Account if the phone number is new.
    """
    return await service.process_new_booking(booking_data)



@router.get("/history", response_model=list[BookingHistoryResponse])

async def get_booking_history(

    current_user: UserResponse = Depends(get_current_customer),

    service: BookingService = Depends(get_booking_service)

):

    """

    Endpoint to fetch the current user's booking history.

    """

    return await service.get_user_dashboard(current_user.user_id)
