# src/services/user_service.py
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from src.repositories.user_respositories import UserRepository
from src.config.telegram_client import telegram_client
class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    async def initiate_fast_login(self, phone: str) -> bool:
        """
        Orchestrates the login request:
        1. Checks if user exists.
        2. Generates the code in DB.
        3. TRIGGERS the actual Telegram message.
        """
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
        """
        Validates the code and prepares the application-level response (Tokens).
        """
        user = self.user_repo.verify_fast_login_code(phone, code)
        if not user:
            return None
            
        # The Repo updated the DB, but the Service creates the "Session"
        # token = self.auth_handler.create_access_token(user_id=user.user_id)
        
        return {
            "access_token": "generated_jwt_token_here",
            "token_type": "bearer",
            "user": {
                "full_name": user.full_name,
                "status": user.status
            }
        }

    def get_profile_with_history(self, user_id: UUID):
        """Combines data from multiple repo methods into one view"""
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return None
            
        cars = self.user_repo.get_user_cars(user_id)
        summary = self.user_repo.get_user_bookings_summary(user_id)
        
        return {
            "profile": user,
            "cars": cars,
            "stats": summary
        }
    
    async def link_and_activate_telegram(self, user_id: UUID, chat_id: int, username: str):
        """
        Flow: User just finished booking and clicked 'Connect Telegram'.
        This upgrades them from GUEST -> ACTIVE.
        """
        # 1. Update DB records
        user = self.user_repo.link_telegram_to_shadow(user_id, chat_id, username)
        
        # 2. Upgrade status
        user = self.user_repo.upgrade_shadow_to_active(user_id)
        
        # 3. Send Welcome Message
        welcome_msg = (
            f"🎉 *Welcome {user.full_name or 'to the Garage'}!*\n\n"
            "Your account is now verified. You can now use this bot to "
            "receive login codes and booking updates."
        )
        await telegram_client.send_message(chat_id, welcome_msg)
        return user