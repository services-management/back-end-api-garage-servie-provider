from .admin_repositories import AdminRepository # Note the file name/class name
from .technical_repositorie import TechnicalRepository 
from .category_repositories import CategoryRepository
from .inventory_repositories import InventoryRepository
from .product_repositories import ProductRepository

__all__ = ["AdminRepository", "TechnicalRepository","CategoryRepository","InventoryRepository","ProductRepository"]