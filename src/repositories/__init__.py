from .admin_repositorie import AdminRepository # Note the file name/class name
from .technical_repositorie import TechnicalRepository 
from .categoryrepository_repositorie import CategoryRepository
from .inventoryrepository_repositorie import InventoryRepository
from .productrepository_repositorie import ProductRepository
# Remove the line 'from .user_repositories import UserRepository'

__all__ = ["AdminRepository", "TechnicalRepository","CategoryRepository","InventoryRepository","ProductRepository"]