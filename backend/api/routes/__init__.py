from backend.api.routes.health import router as health_router
from backend.api.routes.curriculum import router as curriculum_router
from backend.api.routes.config import router as config_router
from backend.api.routes.lecture import router as lecture_router

__all__ = ["health_router", "curriculum_router", "config_router", "lecture_router"]
