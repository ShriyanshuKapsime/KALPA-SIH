from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router
from app.api.routes.classification import router as classification_router

__all__ = ["health_router", "intake_router", "classification_router"]
