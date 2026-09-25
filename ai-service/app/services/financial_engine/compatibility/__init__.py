"""Compatibility package for legacy contract preservation."""
from app.services.financial_engine.compatibility.legacy_adapter import (
    legacy_adapter, LegacyAdapter
)
__all__ = ["legacy_adapter", "LegacyAdapter"]
