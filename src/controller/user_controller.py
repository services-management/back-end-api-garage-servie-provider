from typing import List, Optional
from sqlalchemy.orm import Session
# from src.repositories.user_repositories import user_repository, verify_password
from src.repositories import UserRepository
from src.schemas.user_shema import UserCreate, UserOut
from src.models.user_model import User
from src.utils import verify_password
user_repositories = UserRepository()
class UserController:
    """
    Controller / service layer for user use-cases.
    Orchestrates business logic and delegates persistence to the repository.
    """
    @staticmethod
    def list_users(self, db: Session) -> List[User]:
        return user_repositories.get_all(db)

    @staticmethod
    def get_user(self, db: Session, user_id) -> Optional[User]:
        return user_repositories.get_by_id(db, user_id)

    @staticmethod
    def create_user(self, db: Session, user_in: UserCreate) -> User:
        # here you can add validations, domain rules, events, etc.
        # for now, delegate to repository
        return user_repositories.create_user(
            db=db,
            username=user_in.username,
            password=user_in.password,
            is_admin=user_in.is_admin,
        )

    @staticmethod
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        user = user_repositories.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user


# user_controller = UserController()