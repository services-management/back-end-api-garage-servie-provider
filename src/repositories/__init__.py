from .admin_repository import AdminRepository # Note the file name/class name
from .technical_repository import TechnicalRepository 
from .category_repository import CategoryRepository
from .inventory_repository import InventoryRepository
from .product_repository import ProductRepository
# Remove the line 'from .user_repositories import UserRepository'

__all__ = ["AdminRepository", "TechnicalRepository","CategoryRepository","InventoryRepository","ProductRepository"]