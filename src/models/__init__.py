# src/models/__init__.py (CORRECTED)

# Import and expose all models from the admin and technical files
from .admin import AdminLogin, AdminCreate, AdminUpdate, AdminOut, Token
from .technical import TechnicalOut, TechnicalLogin, TechnicalCreate, TechnicalUpdate # Add all necessary Technical schemas
from .inventory import InventoryCreate, InventoryOut , InventoryUpdate
from .category import CategoryCreate, CategoryResponse
from .product import ProductCreate, ProductResponse , ProductUpdate
# Add other model imports here (e.g., from .user import UserOut)

# The __all__ list should contain all names you want to expose when someone imports from src.models
__all__ = [
    "AdminLogin", "AdminCreate", "AdminUpdate", "AdminOut", "Token",
    "TechnicalOut", "TechnicalLogin", "TechnicalCreate", "TechnicalUpdate",
    "InventoryCreate", "InventoryOut", "InventoryUpdate", "InventoryUpdate",
    "CategoryCreate", "CategoryResponse", "ProductCreate", "ProductResponse", "ProductUpdate"
]