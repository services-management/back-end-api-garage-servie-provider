from .admin import AdminRepository # Note the file name/class name
from .technical import TechnicalRepository 
# Remove the line 'from .user_repositories import UserRepository'

__all__ = ["AdminRepository", "TechnicalRepository"]