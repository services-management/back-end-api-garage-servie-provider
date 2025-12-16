from .admin import AdminRepository # Note the file name/class name
from .technical import TechnicalRepository 
from .categoryrepository import CategoryRepository
from .inventoryrepository import InventoryRepository
from .productrepository import ProductRepository
# Remove the line 'from .user_repositories import UserRepository'

__all__ = ["AdminRepository", "TechnicalRepository","CategoryRepository","InventoryRepository","ProductRepository"]