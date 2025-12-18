# src/models/__init__.py (CLEANED UP)

# Import and expose all models from the *_model.py files
from .admin_model import AdminLogin, AdminCreate, AdminUpdate, AdminOut, Token
from .technical_model import TechnicalOut, TechnicalLogin, TechnicalCreate, TechnicalUpdate
from .inventory_model import InventoryCreate, InventoryOut, InventoryUpdate
from .category_model import CategoryCreate, CategoryResponse
from .product_model import ProductCreate, ProductResponse, ProductUpdate
# Add other model imports here (e.g., from .user_model import UserOut)

# The __all__ list should contain all names you want to expose when someone imports from src.models
__all__ = [
    "AdminLogin", "AdminCreate", "AdminUpdate", "AdminOut", "Token",
    "TechnicalOut", "TechnicalLogin", "TechnicalCreate", "TechnicalUpdate",
    "InventoryCreate", "InventoryOut", "InventoryUpdate",
    "CategoryCreate", "CategoryResponse",
    "ProductCreate", "ProductResponse", "ProductUpdate"
]