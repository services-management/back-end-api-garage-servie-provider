from .admin import router as admin_router
from .technical import router as technical_router

# The __all__ list should contain the actual names being exposed.
# When other files import `from src.routers import *`, they will get these names.
__all__ = ["admin_router", "technical_router"]