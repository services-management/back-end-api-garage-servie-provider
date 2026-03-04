from .admin_router import router as admin_router
from .category_router import router as category_router
from .inventory_router import router as inventory_router
from .product_router import router as product_router
from .service_router import router as service_router
from .technical_router import router as technical_router
from .combo_service_router import router as combo_service_router
from .booking_router import router as booking_router
from .telegram_router import router as telegram_router
from .auth_router import router as auth_router
from .vehicle_router import router as vehicle_router
from .user_router import router as user_router
# The __all__ list should contain the actual names being exposed.
# When other files import `from src.routers import *`, they will get these names.
__all__ = ["admin_router", "technical_router", "product_router", "category_router", "inventory_router", "service_router", "booking_router", "telegram_router", "auth_router","combo_service_router","vehicle_router", "user_router"]
