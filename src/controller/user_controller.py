# src/services/user_service.py
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from src.repositories.user_respositories import UserRepository
from src.config.telegram_client import telegram_client
from src.models.user_model import CustomerVehicleCreate, CustomerVehicleUpdate

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    async def initiate_fast_login(self, phone: str) -> bool:
        user = self.user_repo.get_user_by_phone(phone)
        if not user or not user.telegram_chat_id:
            return False
        code = self.user_repo.generate_fast_login_code(phone)
        if not code:
            return False
            
        message = f"🚗 *Your Fast Login Code*\n\nYour verification code is: `{code}`\n\n_Valid for 5 minutes._"
        await telegram_client.send_message(user.telegram_chat_id, message)
        return True

    async def confirm_fast_login(self, phone: str, code: str) -> Optional[Dict[str, Any]]:
        user = self.user_repo.verify_fast_login_code(phone, code)
        if not user:
            return None
        return {
            "access_token": "mock_token",
            "token_type": "bearer",
            "user": user
        }

    def get_profile_with_history(self, user_id: UUID):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return None
        cars = self.user_repo.get_user_cars(user_id)
        summary = self.user_repo.get_user_bookings_summary(user_id)
        return {
            "profile": user,
            "saved_vehicles": cars,
            "stats": summary
        }
    
    async def update_profile(self, user_id: UUID, full_name: str):
        return self.user_repo.update_user(user_id, {"full_name": full_name})

    async def set_password(self, user_id: UUID, password: str):
        from src.utils.hash_password import hash_password
        hashed = hash_password(password)
        return self.user_repo.update_user(user_id, {"password_hash": hashed, "is_active": True})

    async def add_vehicle(self, user_id: UUID, payload: CustomerVehicleCreate):
        return self.user_repo.add_user_car(user_id, payload)

    async def get_my_vehicles(self, user_id: UUID):
        return self.user_repo.get_user_cars(user_id)

    async def update_vehicle(self, user_id: UUID, vehicle_id: int, payload: CustomerVehicleUpdate):
        return self.user_repo.update_user_car(user_id, vehicle_id, payload)

    async def delete_vehicle(self, user_id: UUID, vehicle_id: int):
        return self.user_repo.delete_user_car(user_id, vehicle_id)

    async def link_and_activate_telegram(self, user_id: UUID, chat_id: int, username: str):
        user = self.user_repo.link_telegram_to_shadow(user_id, chat_id, username)
        user = self.user_repo.upgrade_shadow_to_active(user_id)
        welcome_msg = f"🎉 *Welcome {user.full_name or 'to the Garage'}!*\n\nVerified."
        await telegram_client.send_message(chat_id, welcome_msg)
        return user
