from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.models.user import User
import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class UserRepository:
    """Repository for User database operations."""

    def get_all(self, db: Session) -> List[User]:
        """Get all users from the database."""
        return db.query(User).all()

    def get_by_id(self, db: Session, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get a user by username."""
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, username: str, password: str, is_admin: bool = False) -> User:
        """Create a new user with hashed password."""
        hashed_password = hash_password(password)
        db_user = User(
            username=username,
            password=hashed_password,
            is_admin=is_admin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def create_admin_user_if_not_exists(self, db: Session):
        """Create admin user if it doesn't exist."""
        admin_user = self.get_by_username(db, "admin")
        if not admin_user:
            self.create_user(db, username="admin", password="admin", is_admin=True)


user_repository = UserRepository()
