"""
Canonical Financial Amount and Currency Parser.
Distinguishes financial capital from non-monetary units (customers, sq ft, experience, livestock),
identifies explicit vs context-inferred INR currency sources, emits diagnostic logging,
and provides extraction provenance.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from app.core.logging import logger
from app.services.intake.language_normalizer import normalize_unicode_text
from app.services.intake.indic_number_parser import parse_indic_number_expression, parse_compositional_indic_number

# Explicit Currency Regex: handles Indic script tokens directly and Latin tokens with word boundaries
EXPLICIT_CURRENCY_REGEX = re.compile(
    r"(?:₹|रू\.?|ರೂ\.?|रुपये|रुपए|रूपये|रूपए|रुपया|ರೂಪಾಯಿ|ರೂಪಾಯಿಗಳು|ரூபாய்|రూపాయలు|টাকা|રૂપિયા|ਰੁਪਏ|\b(?:rs\.?|inr|rupees?|rupaye?|rupee)\b)",
    re.IGNORECASE
)

# Contextual Capital / Investment Markers
FINANCIAL_CONTEXT_REGEX = re.compile(
    r"(?:बजट|पूंजी|पूँजी|निवेश|लागत|ಬಂಡವಾಳ|ಹೂಡಿಕೆ|भांडवल|गुंतवणूक|முதலீடு|పెట్టుబడి|\b(?:budget|capital|invest|investing|investment|funds|savings|margin|mere\s+paas|mera\s+budget|lagane\s+ke\s+liye|lagane|kharch|lagat)\b)",
    re.IGNORECASE
)

# Non-Financial Units to Exclude (Negative Test Filters)
NON_FINANCIAL_UNIT_PATTERNS = [
    # Customers / People / Users
    r"(?:customers?|clients?|users?|people|visitors?|buyers?|subscribers?|ग्राहक|लोग|कस्टमर|यूजर्स|ಗ್ರಾಹಕರು|ಜನರು|வாடிக்கையாளர்கள்|மக்கள்)",

    # Area / Real Estate
    r"(?:sq\s*ft|sqft|square\s*feet|square\s*foot|acres?|gunta|hectares?|cent|वर्ग\s*फुट|वर्ग\s*फिट|एकड़|गुंठा|हेक्टेयर|ಚದರ\s*ಅಡಿ|ಎಕರೆ)",

    # Experience / Time
    r"(?:years?|yrs?|months?|days?|hours?|ವರ್ಷ|ವರ್ಷಗಳ|साल|वर्ष|महिने)",

    # Livestock / Goods Units
    r"(?:cows?|cattle|buffaloes?|hens?|chickens?|birds?|goats?|sheep|गाय|भैंस|मुर्गी|मुर्गियां|बकरी|बकरियां|पशु|ಹಸುಗಳು|ಎಮ್ಮೆಗಳು|ಕೋಳಿಗಳು|ಕುರಿಗಳು|ಮೇಕೆಗಳು)",

    # Volume / Weight
    r"(?:litres?|liters?|ltr|kg|kgs|kilograms?|tons?|quintals?|क्विंटल|लीटर|किलो)"
]


@dataclass
class AmountProvenance:
    value: int
    currency: str
    currency_source: str  # "EXPLICIT" | "CONTEXT_INFERRED"
    source_text: str
    normalized_text: str
    method: str  # "INDIC_NUMBER_COMPOSITION" | "EXPLICIT_CURRENCY" | "NUMERIC_SCALE" | "CONTEXT_INFERRED"
    language: str
    confidence: float


@dataclass
class AmountResult:
    available_capital: Optional[int]
    currency: str
    currency_source: str  # "EXPLICIT" | "CONTEXT_INFERRED" | "NONE"
    loan_requested: Optional[int] = None
    provenance: Optional[AmountProvenance] = None


def has_non_financial_unit_association(text: str) -> bool:
    """
    Checks if the sentence contains an explicit non-financial unit associated with a quantity
    (e.g., 'one lakh customers', '1 lakh sq ft', '5 years of experience', '100 cows').
    """
    clean = text.lower()
    for pat in NON_FINANCIAL_UNIT_PATTERNS:
        # Check: [number or scale] [optional 'of'] [non-financial unit]
        num_unit_regex = rf"(?:[0-9]+|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|lakh|lac|crore|एक|दो|तीन|चार|पांच|पाँच|छह|सात|आठ|नौ|दस|सौ|हजार|हज़ार|लाख|करोड़|करोड़)\b)\s*(?:of\s+)?{pat}\b"
        if re.search(num_unit_regex, clean, re.IGNORECASE):
            return True
    return False


def parse_canonical_amount(
    text: str,
    language_code: str = "en"
) -> AmountResult:
    """
    Main entrypoint for canonical amount extraction.
    Ensures:
    - Rejection of non-financial metrics (customers, sq ft, etc.)
    - INR default inference (EXPLICIT vs CONTEXT_INFERRED)
    - Distinguishes loan requests from available investment capital
    - Structured diagnostic logging: [AMOUNT EXTRACTION]
    - Provenance generation
    """
    if not text or not text.strip():
        return AmountResult(available_capital=None, currency="INR", currency_source="NONE")

    clean = normalize_unicode_text(text)
    lower = clean.lower()

    # 1. Negative Unit Filter: Check if the text is describing non-financial units
    if has_non_financial_unit_association(clean):
        # Only reject if there is NO explicit currency marker or financial context marker
        has_curr = bool(EXPLICIT_CURRENCY_REGEX.search(lower))
        has_fctx = bool(FINANCIAL_CONTEXT_REGEX.search(lower))
        if not has_curr and not has_fctx:
            logger.info(f"[AMOUNT REJECTED NON-FINANCIAL] Text '{text[:50]}' contains non-financial metric.")
            return AmountResult(available_capital=None, currency="INR", currency_source="NONE")

    # 2. Check for explicit currency and financial context
    has_explicit_currency = bool(EXPLICIT_CURRENCY_REGEX.search(lower))
    has_financial_context = bool(FINANCIAL_CONTEXT_REGEX.search(lower))

    # 3. Check for Loan distinction
    is_loan_text = bool(re.search(r"\b(?:loan|ऋण|कर्ज|लोन|ಸಾಲ|கடன்)\b", lower))

    # 4. Extract candidates
    valid_amount: Optional[int] = None
    chosen_phrase: str = ""
    chosen_method: str = "INDIC_NUMBER_COMPOSITION"

    # Pattern A: Currency prefixed e.g. "₹1,00,000", "Rs 1.5 lakh", "INR 2.5 lakh"
    curr_prefix_pat = r"(?:₹|rs\.?|inr|रू\.?|ರೂ\.?)\s*([0-9a-zA-Z\u0900-\u0D7F\s\.,]+?)(?=[,\.\?!]|\s+(?:hai|and|in|with|mein|me|for|$)|$)"
    m_pref = re.search(curr_prefix_pat, clean, re.IGNORECASE)
    if m_pref:
        matched_text = m_pref.group(0).strip()
        val = parse_indic_number_expression(matched_text) or parse_indic_number_expression(m_pref.group(1).strip())
        if val and val > 0:
            valid_amount = val
            chosen_phrase = matched_text
            chosen_method = "EXPLICIT_CURRENCY"

    # Pattern B: Currency suffixed e.g. "एक लाख रुपये", "one lakh rupees", "2 lakh rupaye"
    if valid_amount is None:
        curr_suffix_pat = r"([0-9a-zA-Z\u0900-\u0D7F\s\.,]+?)\s*(?:rupees|rupee|रुपये|रुपए|रूपये|रुपया|రూపాయలు|ரூபாய்|ರೂಪಾಯಿಗಳು|ರೂಪಾಯಿ)"
        m_suff = re.search(curr_suffix_pat, clean, re.IGNORECASE)
        if m_suff:
            matched_text = m_suff.group(0).strip()
            val = parse_indic_number_expression(matched_text) or parse_indic_number_expression(m_suff.group(1).strip())
            if val and val > 0:
                valid_amount = val
                chosen_phrase = matched_text
                chosen_method = "EXPLICIT_CURRENCY"

    # Pattern C: Budget / Contextual phrase e.g. "budget ek lakh", "बजट दो लाख पचास हजार"
    if valid_amount is None:
        budget_pat = r"(?:budget|capital|invest|investment|बजट|पूंजी|निवेश|लागत|ಬಂಡವಾಳ|ಹೂಡಿಕೆ|भांडवल|mere paas|mera budget)\s*(?:is|of|hai|mein|me|around|लगभग)?\s*([0-9a-zA-Z\u0900-\u0D7F\s\.,]+?)(?=[,\.\?!]|\s+(?:hai|and|in|mein|me|$)|$)"
        m_bud = re.search(budget_pat, clean, re.IGNORECASE)
        if m_bud:
            matched_text = m_bud.group(0).strip()
            val = parse_indic_number_expression(m_bud.group(1).strip()) or parse_indic_number_expression(matched_text)
            if val and val > 0:
                valid_amount = val
                chosen_phrase = matched_text
                chosen_method = "INDIC_NUMBER_COMPOSITION"

    # Pattern D: Direct Compositional number parsing
    if valid_amount is None:
        direct_val = parse_indic_number_expression(clean)
        if direct_val and direct_val > 0:
            # Check if input has currency, financial context, or is a pure short amount reply (<= 4 words)
            is_short_reply = len(clean.split()) <= 4
            if has_explicit_currency or has_financial_context or is_short_reply:
                valid_amount = direct_val
                chosen_phrase = clean
                chosen_method = "INDIC_NUMBER_COMPOSITION"

    if valid_amount is None:
        return AmountResult(available_capital=None, currency="INR", currency_source="NONE")

    # Determine currency source
    currency_source = "EXPLICIT" if has_explicit_currency else "CONTEXT_INFERRED"

    # Distinguish loan requests vs available capital
    loan_requested = None
    available_capital = valid_amount

    if is_loan_text and not has_financial_context:
        loan_requested = valid_amount
        available_capital = None

    # Diagnostic Logging
    logger.info(
        f"[AMOUNT EXTRACTION] raw_phrase=\"{chosen_phrase}\" "
        f"normalized_phrase=\"{normalize_unicode_text(chosen_phrase)}\" "
        f"parsed_amount={valid_amount} "
        f"currency=INR "
        f"method={chosen_method}"
    )

    provenance = AmountProvenance(
        value=valid_amount,
        currency="INR",
        currency_source=currency_source,
        source_text=chosen_phrase,
        normalized_text=normalize_unicode_text(chosen_phrase),
        method=chosen_method,
        language=language_code,
        confidence=0.98 if currency_source == "EXPLICIT" else 0.92
    )

    return AmountResult(
        available_capital=available_capital,
        currency="INR",
        currency_source=currency_source,
        loan_requested=loan_requested,
        provenance=provenance
    )
