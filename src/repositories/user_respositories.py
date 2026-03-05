import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.schemas.booking import User, UserStatus, Booking, BookingStatus, UserVehicle

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def create_shadow_account(self, phone: str, full_name: Optional[str] = None) -> User:
        user = User(
            phone=phone,
            full_name=full_name,
            role=UserStatus.GUEST,
            is_active=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_bookings_summary(self, user_id: UUID) -> Dict[str, Any]:
        try:
            total_bookings = self.db.query(Booking).filter(Booking.user_id == user_id).count()
            upcoming_bookings = self.db.query(Booking).filter(
                Booking.user_id == user_id,
                Booking.appointment_date >= date.today(),
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).count()
            user = self.get_user_by_id(user_id)
            return {
                'total_bookings': total_bookings,
                'upcoming_bookings': upcoming_bookings,
                'user_status': user.role if user else None
            }
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return {'total_bookings': 0, 'upcoming_bookings': 0, 'user_status': None}

    # --- Vehicle Management ---

    def add_user_car(self, user_id: UUID, car_data: Any) -> UserVehicle:
        vehicle = UserVehicle(
            user_id=user_id,
            car_make=car_data.car_make,
            car_model=car_data.car_model,
            car_year=getattr(car_data, 'car_year', None),
            car_engine=getattr(car_data, 'car_engine', None),
            license_plate=getattr(car_data, 'license_plate', None)
        )
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_user_cars(self, user_id: UUID) -> List[UserVehicle]:
        return self.db.query(UserVehicle).filter(UserVehicle.user_id == user_id).all()

    def update_user_car(self, user_id: UUID, vehicle_id: int, car_data: Any) -> Optional[UserVehicle]:
        vehicle = self.db.query(UserVehicle).filter(
            UserVehicle.vehicle_id == vehicle_id,
            UserVehicle.user_id == user_id
        ).first()
        if vehicle:
            update_dict = car_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(vehicle, key):
                    setattr(vehicle, key, value)
            self.db.commit()
            self.db.refresh(vehicle)
        return vehicle

    def delete_user_car(self, user_id: UUID, vehicle_id: int) -> bool:
        vehicle = self.db.query(UserVehicle).filter(
            UserVehicle.vehicle_id == vehicle_id,
            UserVehicle.user_id == user_id
        ).first()
        if vehicle:
            self.db.delete(vehicle)
            self.db.commit()
            return True
        return False

    def upgrade_shadow_to_active(self, user_id: UUID) -> User:
        return self.update_user(user_id, {"role": UserStatus.ACTIVE, "is_active": True})

    def link_telegram_to_shadow(self, user_id: UUID, chat_id: int, username: str) -> User:
        return self.update_user(user_id, {"telegram_chat_id": chat_id, "telegram_username": username})

    def get_user_by_telegram_chat_id(self, chat_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.telegram_chat_id == chat_id).first()

    def has_booking_conflict(self, user_id: UUID, appointment_date: date, start_time: Any) -> bool:
        """
        Check if the user already has a pending or confirmed booking at the same date/time.
        """
        existing = self.db.query(Booking).filter(
            Booking.user_id == user_id,
            Booking.appointment_date == appointment_date,
            Booking.start_time == start_time,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).first()
        return existing is not None
