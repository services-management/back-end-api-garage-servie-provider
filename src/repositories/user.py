from typing import List, Optional
from uuid import UUID
from src.models.user import User
import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


class UserRepository:
    def __init__(self):
        self.users: List[User] = []
        self._create_admin_user()

    def _create_admin_user(self):
        admin_user = self.get_by_username("admin")
        if not admin_user:
            self.create_user(
                User(
                    username="admin",
                    password="admin",
                    is_admin=True,
                )
            )

    def get_all(self) -> List[User]:
        return self.users

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return next((user for user in self.users if user.id == user_id), None)

    def get_by_username(self, username: str) -> Optional[User]:
        return next((user for user in self.users if user.username == username), None)

    def create_user(self, user: User) -> User:
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed_password.decode('utf-8')
        self.users.append(user)
        return user


user_repository = UserRepository()
