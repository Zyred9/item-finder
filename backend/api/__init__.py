from .auth import router as auth_router
from .families import router as families_router
from .items import router as items_router
from .categories import router as categories_router
from .reminders import router as reminders_router
from .chat import router as chat_router
from .debug import router as debug_router

__all__ = [
    "auth_router", "families_router", "items_router",
    "categories_router", "reminders_router", "chat_router",
    "debug_router"
]