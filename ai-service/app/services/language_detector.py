"""
Language Detector Module for KALPA.
Delegates to the centralized language normalizer in app.services.intake.language_normalizer.
"""

from typing import Tuple, Optional
from app.services.intake.language_normalizer import (
    detect_language_multilingual,
    LANGUAGE_METADATA
)

# Export legacy LANGUAGE_MAP for compatibility
LANGUAGE_MAP = {k: v["name"] for k, v in LANGUAGE_METADATA.items()}


def detect_language(text: str, override_code: Optional[str] = None) -> Tuple[str, str]:
    """
    Deterministically detects language code and human-readable name for given text.
    Returns (code, name) e.g. ('hi', 'Hindi'), ('en', 'English'), ('kn', 'Kannada').
    """
    if override_code and override_code in LANGUAGE_MAP:
        return override_code, LANGUAGE_MAP[override_code]

    info = detect_language_multilingual(text, hint_code=override_code)
    return info.code, info.name
