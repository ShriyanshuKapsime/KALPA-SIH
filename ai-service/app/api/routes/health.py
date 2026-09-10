from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.health import HealthResponse
from app.database.session import get_db
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(tags=["Health"])


@router.get("/", response_model=Dict[str, str])
def root():
    """
    Root status endpoint.
    """
    return {
        "service": "KALPA AI Service",
        "status": "running",
    }


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint for the FastAPI AI Backend.
    """
    db_ok = False
    if db is not None:
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as e:
            logger.warning(f"Database health check probe failed: {e}")
            db_ok = False

    return HealthResponse(
        status="healthy",
        service="kalpa-ai-service",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_ok,
        spatial_enabled=settings.POSTGIS_ENABLED,
        vector_enabled=settings.PGVECTOR_ENABLED,
    )

