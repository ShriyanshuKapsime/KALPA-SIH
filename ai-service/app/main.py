from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.routes import health_router, intake_router, classification_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown routines.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"Tagline: {settings.TAGLINE}")
    try:
        from app.database.base import Base
        from app.database.session import engine
        from app.services.sarvam_service import log_sarvam_config
        import app.database.models  # Ensure all models are loaded
        if engine is not None:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized successfully.")
        log_sarvam_config()
    except Exception as e:
        logger.warning(f"Database table initialization deferred/skipped: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


def create_application() -> FastAPI:
    """
    Factory creating configured FastAPI instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=f"{settings.TAGLINE}\n\nSIH 2026 Prototype Architecture.",
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Route Handlers
    app.include_router(health_router)
    app.include_router(intake_router, prefix=settings.API_V1_STR)
    app.include_router(classification_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
