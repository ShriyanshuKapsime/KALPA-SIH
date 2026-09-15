"""
KALPA Stage 1 Multilingual Intake & Canonical Extraction Engine.
Provides deterministic language normalization, compositional Indic number parsing,
contextual amount extraction with provenance, and resilient entity extraction.
"""

from app.services.intake.language_normalizer import (
    LanguageInfo,
    normalize_unicode_text,
    normalize_indic_numerals,
    detect_language_multilingual,
)
from app.services.intake.indic_number_parser import (
    parse_indic_number_expression,
    parse_compositional_indic_number,
)
from app.services.intake.amount_parser import (
    AmountResult,
    AmountProvenance,
    parse_canonical_amount,
)
from app.services.intake.business_entity_extractor import (
    BusinessEntityResult,
    extract_multilingual_business_entities,
)
from app.services.intake.canonical_extractor import (
    CanonicalIntakeExtractor,
    canonical_intake_extractor,
)

__all__ = [
    "LanguageInfo",
    "normalize_unicode_text",
    "normalize_indic_numerals",
    "detect_language_multilingual",
    "parse_indic_number_expression",
    "parse_compositional_indic_number",
    "AmountResult",
    "AmountProvenance",
    "parse_canonical_amount",
    "BusinessEntityResult",
    "extract_multilingual_business_entities",
    "CanonicalIntakeExtractor",
    "canonical_intake_extractor",
]
