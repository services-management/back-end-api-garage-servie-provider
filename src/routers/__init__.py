from .admin import router as admin_router
from .technical import router as technical_router
from .product import router as product_router
from .category import router as category_router
from .inventory import router as inventory_router

# The __all__ list should contain the actual names being exposed.
# When other files import `from src.routers import *`, they will get these names.
__all__ = ["admin_router", "technical_router","product_router","category_router","inventory_router"]