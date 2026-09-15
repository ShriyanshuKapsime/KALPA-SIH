"""
Backward-compatibility adapter for money normalization.
Delegates to the canonical intake amount parser and indic number parser.
"""

from typing import Optional, Tuple
from app.services.intake.language_normalizer import normalize_indic_numerals, normalize_unicode_text
from app.services.intake.amount_parser import parse_canonical_amount
from app.services.intake.indic_number_parser import BASE_WORDS as NUMBER_WORDS, SCALES as UNIT_MULTIPLIERS


def normalize_indic_digits(text: str) -> str:
    """Converts Kannada and Devanagari numerals to standard ASCII digits."""
    return normalize_indic_numerals(text)


def parse_indian_money(text: str) -> Tuple[Optional[int], str]:
    """
    Extracts and normalizes Indian currency expressions to integer amount in INR.
    Supports English, Kannada, Hindi, Marathi, Tamil, Telugu words, numbers, compositions,
    fractions, and compact abbreviations.
    """
    if not text or not text.strip():
        return None, "INR"

    result = parse_canonical_amount(text)
    return result.available_capital, result.currency
