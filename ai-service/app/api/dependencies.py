"""
FastAPI Dependencies: DB session, settings, and auth token checks.
"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.config import settings, Settings


def get_settings() -> Settings:
    return settings


# Re-export get_db for convenient dependency injection
__all__ = ["get_db", "get_settings"]
