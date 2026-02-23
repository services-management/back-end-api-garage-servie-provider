# src/models/__init__.py (CORRECTED)

# Import and expose all models from the admin and technical files
from .admin_model import AdminCreate, AdminLogin, AdminOut, AdminUpdate, Token
from .category_model import CategoryCreate, CategoryResponse
from .inventory_model import InventoryCreate, InventoryOut, InventoryUpdate
from .product_model import ProductCreate, ProductResponse, ProductUpdate
from .technical_model import (  # Add all necessary Technical schemas
    TechnicalCreate, TechnicalLogin, TechnicalOut, TechnicalUpdate)
from .vehicle_model import(
    VehicleCreate,MakeBase,ModelBase,VehicleUpdate
)
# Add other model imports here (e.g., from .user import UserOut)

# The __all__ list should contain all names you want to expose when someone imports from src.models
__all__ = [
    "AdminLogin", "AdminCreate", "AdminUpdate", "AdminOut", "Token",
    "TechnicalOut", "TechnicalLogin", "TechnicalCreate", "TechnicalUpdate",
    "InventoryCreate", "InventoryOut", "InventoryUpdate", "InventoryUpdate",
    "CategoryCreate", "CategoryResponse", "ProductCreate", "ProductResponse", "ProductUpdate",
    "VehicleCreate","MakeBase","ModelBase","VehicleUpdate"
]