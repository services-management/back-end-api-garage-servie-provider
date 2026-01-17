from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select, text
from sqlalchemy.exc import IntegrityError, NoResultFound
import logging
import random

from src.models.user import User, UserStatus
from src.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse,
    UserFilter,
    TelegramLink
)

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for handling all user database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== FLOW 1: "No Account" Flow ====================
    
    def create_shadow_account(self, phone: str, full_name: Optional[str] = None) -> User:
        """
        Step 3: Auto-Creation of shadow account
        Used when booking without existing account
        """
        try:
            # Check if phone already exists
            existing_user = self.get_user_by_phone(phone)
            if existing_user:
                return existing_user  # Return existing user
            
            # Create shadow account
            user = User(
                phone=phone,
                full_name=full_name,
                status=UserStatus.GUEST,
                is_active=False  # Shadow account
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Shadow account created: {user.user_id} (phone: {phone})")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating shadow account: {str(e)}")
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating shadow account: {str(e)}")
            raise
    
    def link_telegram_to_shadow(self, user_id: UUID, 
                               telegram_chat_id: int, 
                               telegram_username: str = None) -> User:
        """
        Step 5: Link Telegram after booking
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Check if Telegram is already linked to another account
            existing = self.get_user_by_telegram_chat_id(telegram_chat_id)
            if existing and existing.user_id != user_id:
                raise ValueError("Telegram account already linked to another user")
            
            user.telegram_chat_id = telegram_chat_id
            user.telegram_username = telegram_username
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Telegram linked to shadow account {user_id}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error linking Telegram to shadow account: {str(e)}")
            raise
    
    # ==================== FLOW 2: "Existing User" Flow ====================
    
    def generate_fast_login_code(self, phone: str) -> Optional[str]:
        """
        Step 1: Generate 4-digit Fast Login code and send via Telegram
        """
        try:
            user = self.get_user_by_phone(phone)
            if not user:
                return None  # User not found
            
            # Check if user has Telegram linked
            if not user.telegram_chat_id:
                raise ValueError("User doesn't have Telegram linked")
            
            # Check if can request new code
            if not user.can_request_verification():
                raise ValueError("Please wait before requesting new code")
            
            # Generate 4-digit code
            code = str(random.randint(1000, 9999))
            
            # Store code
            user.verification_code = code
            user.verification_sent_at = datetime.utcnow()
            user.verification_attempts = 0
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Return code (in real app, send via Telegram bot)
            logger.info(f"Fast login code generated for {phone}: {code}")
            return code
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating fast login code: {str(e)}")
            raise
    
    def verify_fast_login_code(self, phone: str, code: str) -> Optional[User]:
        """
        Step 1: Verify 4-digit Fast Login code
        """
        try:
            user = self.get_user_by_phone(phone)
            if not user:
                return None
            
            # Check if code exists and not expired
            if not user.verification_code:
                return None
            
            if user.is_verification_expired():
                raise ValueError("Verification code expired")
            
            # Check attempts
            if user.verification_attempts >= 3:
                raise ValueError("Too many attempts")
            
            # Verify code
            if user.verification_code != code:
                user.verification_attempts += 1
                self.db.commit()
                return None
            
            # Code verified - mark user as active and update
            user.status = UserStatus.ACTIVE
            user.verified_at = datetime.utcnow()
            user.last_login = datetime.utcnow()
            user.verification_code = None  # Clear code after successful verification
            user.verification_attempts = 0
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Fast login successful for {phone}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error verifying fast login code: {str(e)}")
            raise
    
    def upgrade_shadow_to_active(self, user_id: UUID) -> User:
        """
        Upgrade shadow account to active when they verify via Telegram
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            if user.status == UserStatus.ACTIVE:
                return user  # Already active
            
            user.status = UserStatus.ACTIVE
            user.verified_at = datetime.utcnow()
            user.is_active = True
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Shadow account upgraded to active: {user_id}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upgrading shadow to active: {str(e)}")
            raise
    
    # ==================== CAR HISTORY TRACKING ====================
    
    def get_user_cars(self, user_id: UUID) -> List[Dict[str, str]]:
        """
        Step 2: Get user's car history from their bookings
        """
        try:
            from src.models.booking import Booking
            
            # Get unique car make/model combinations from user's bookings
            cars = self.db.query(
                Booking.car_make,
                Booking.car_model,
                func.max(Booking.appointment_date).label('last_used')
            ).filter(
                Booking.user_id == user_id
            ).group_by(
                Booking.car_make,
                Booking.car_model
            ).order_by(
                func.max(Booking.appointment_date).desc()
            ).all()
            
            return [
                {
                    'car_make': car_make,
                    'car_model': car_model,
                    'last_used': last_used
                }
                for car_make, car_model, last_used in cars
            ]
        except Exception as e:
            logger.error(f"Error getting user cars: {str(e)}")
            return []
    
    # ==================== BASIC CRUD OPERATIONS ====================
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Step 2: Backend Check - Find user by phone"""
        try:
            return self.db.query(User).filter(User.phone == phone).first()
        except Exception as e:
            logger.error(f"Error fetching user by phone {phone}: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: UUID, include_bookings: bool = False) -> Optional[User]:
        try:
            query = self.db.query(User)
            if include_bookings:
                query = query.options(joinedload(User.bookings))
            return query.filter(User.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}")
            return None
    
    def get_user_by_telegram_chat_id(self, telegram_chat_id: int) -> Optional[User]:
        try:
            return self.db.query(User).filter(
                User.telegram_chat_id == telegram_chat_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching user by Telegram chat ID {telegram_chat_id}: {str(e)}")
            return None
    
    def get_user_by_telegram_username(self, telegram_username: str) -> Optional[User]:
        try:
            return self.db.query(User).filter(
                func.lower(User.telegram_username) == func.lower(telegram_username)
            ).first()
        except Exception as e:
            logger.error(f"Error fetching user by Telegram username {telegram_username}: {str(e)}")
            return None
    
    def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found for update")
                return None
            
            # Handle phone update
            if 'phone' in update_data and update_data['phone'] != user.phone:
                existing_user = self.get_user_by_phone(update_data['phone'])
                if existing_user and existing_user.user_id != user_id:
                    raise ValueError("Phone number already in use")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(user, field) and value is not None:
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            return user
            
        except ValueError as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    def update_last_login(self, user_id: UUID) -> None:
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.last_login = datetime.utcnow()
                user.updated_at = datetime.utcnow()
                self.db.commit()
                logger.debug(f"Updated last login for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
    
    def get_users_with_filters(self, filters: UserFilter) -> Tuple[List[User], int]:
        try:
            query = self.db.query(User)
            
            # Apply filters
            if filters.status:
                query = query.filter(User.status == filters.status)
            if filters.is_active is not None:
                query = query.filter(User.is_active == filters.is_active)
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(or_(
                    User.phone.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.telegram_username.ilike(search_term)
                ))
            if filters.phone:
                query = query.filter(User.phone.ilike(f"%{filters.phone}%"))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            query = query.order_by(User.created_at.desc())
            query = query.limit(filters.per_page).offset(
                (filters.page - 1) * filters.per_page
            )
            
            return query.all(), total_count
        except Exception as e:
            logger.error(f"Error fetching users with filters: {str(e)}")
            return [], 0
    
    # ==================== BOOKING CONFLICT CHECK ====================
    
    def has_booking_conflict(self, user_id: UUID, 
                           appointment_date: date, 
                           start_time: time) -> bool:
        """
        Step 3: Conflict Check
        Check if user already has booking at same time
        """
        try:
            from src.models.booking import Booking, BookingStatus
            
            conflicting_bookings = self.db.query(Booking).filter(
                Booking.user_id == user_id,
                Booking.appointment_date == appointment_date,
                Booking.start_time == start_time,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).count()
            
            return conflicting_bookings > 0
        except Exception as e:
            logger.error(f"Error checking booking conflict: {str(e)}")
            return True  # Assume conflict if error
    
    def get_user_bookings_summary(self, user_id: UUID) -> Dict[str, Any]:
        """Get summary of user's bookings"""
        try:
            from src.models.booking import Booking, BookingStatus
            
            total_bookings = self.db.query(Booking).filter(
                Booking.user_id == user_id
            ).count()
            
            upcoming_bookings = self.db.query(Booking).filter(
                Booking.user_id == user_id,
                Booking.appointment_date >= date.today(),
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).count()
            
            return {
                'total_bookings': total_bookings,
                'upcoming_bookings': upcoming_bookings,
                'user_status': self.get_user_by_id(user_id).status if self.get_user_by_id(user_id) else None
            }
        except Exception as e:
            logger.error(f"Error getting user bookings summary: {str(e)}")
            return {
                'total_bookings': 0,
                'upcoming_bookings': 0,
                'user_status': None
            }