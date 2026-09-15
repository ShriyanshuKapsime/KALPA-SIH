"""
Deterministic Language and Unicode Normalization Layer.
Provides Indic digit conversion, Unicode normalization, Nukta unification,
and multi-signal language detection across English, Hindi, Kannada, Marathi, Tamil,
Telugu, Bengali, Gujarati, Malayalam, Punjabi, Odia, and Hinglish.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Set

# Standard Indic Numeral Translation Tables to ASCII digits (0-9)
INDIC_DIGIT_MAPS = {
    "devanagari": str.maketrans("०१२३४५६७८९", "0123456789"),
    "kannada": str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789"),
    "bengali": str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"),
    "gujarati": str.maketrans("૦૧૨૩૪૫೬૭૮૯", "0123456789"),
    "gurmukhi": str.maketrans("੦੧੨੩੪੫੬੭੮੯", "0123456789"),
    "odia": str.maketrans("୦୧୨୩۴୫୬୭୮୯", "0123456789"),
    "tamil": str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789"),
    "telugu": str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789"),
    "malayalam": str.maketrans("൦൧൨൩൪൫൬൭൮൯", "0123456789"),
}

# ISO 639-1 code to Locale and Full Display Name
LANGUAGE_METADATA: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "locale": "en-IN"},
    "hi": {"name": "Hindi", "locale": "hi-IN"},
    "kn": {"name": "Kannada", "locale": "kn-IN"},
    "mr": {"name": "Marathi", "locale": "mr-IN"},
    "ta": {"name": "Tamil", "locale": "ta-IN"},
    "te": {"name": "Telugu", "locale": "te-IN"},
    "gu": {"name": "Gujarati", "locale": "gu-IN"},
    "bn": {"name": "Bengali", "locale": "bn-IN"},
    "ml": {"name": "Malayalam", "locale": "ml-IN"},
    "pa": {"name": "Punjabi", "locale": "pa-IN"},
    "or": {"name": "Odia", "locale": "or-IN"},
    "od": {"name": "Odia", "locale": "or-IN"},
    "ur": {"name": "Urdu", "locale": "ur-IN"},
}

# Lexical markers for Devanagari disambiguation (Hindi vs Marathi)
MARATHI_LEXICAL_MARKERS: Set[str] = {
    "माझ्या", "गावात", "आहे", "करायचा", "दुकानाचा", "सुरू", "व्यवसाय",
    "आम्ही", "करतो", "आहेत", "चालू", "करावा", "सांगा", "माझे", "करायचे", "इच्छितो",
    "दुकान", "भांडवल", "रुपये", "पैसे", "होते", "शिलाई", "शेती", "नाही", "दीड", "अडीच",
    "सव्वा", "पाऊण", "पन्नास", "चाळीस", "साठ", "सत्तर", "ऐंशी", "नव्वद", "शंभर", "दोन", "पाच", "दहा"
}

HINDI_LEXICAL_MARKERS: Set[str] = {
    "मुझे", "अपने", "गांव", "गाँव", "में", "दुकान", "शुरू", "करनी", "करना", "है", "मेरे",
    "पास", "रुपये", "रुपए", "रूपये", "चाहता", "हूँ", "हूं", "चाहती", "कारोबार",
    "खोलना", "खोलनी", "व्यापार", "लाख", "हजार", "हज़ार", "करोड़", "करोड़", "खेती", "सिलाई", "अनुभव",
    "डेढ़", "ढाई", "साढ़े", "पचास", "चालीस", "बीस", "तीस", "साठ", "सत्तर", "अस्सी", "नब्बे", "सौ"
}

# Distinctive Hinglish lexical markers (strictly Hindi/Indic vocabulary in Latin script)
HINGLISH_LEXICAL_MARKERS: Set[str] = {
    "mera", "meri", "mere", "mujhe", "muze", "kholna", "kholni", "shuru", "karna",
    "karni", "chahiye", "paas", "rupaye", "rupay", "rupya", "karod",
    "dukan", "dukaan", "dokan", "vyapar", "anubhav", "mein",
    "paanch", "panch", "chhah", "chhe", "saat", "aath", "nau", "das",
    "gyarah", "barah", "dedh", "dhai", "sadhe", "pachaas", "pachas", "kirana",
    "chahta", "chahti", "lagana", "paisa", "paise", "hoga", "hogi"
}


@dataclass
class LanguageInfo:
    code: str
    locale: str
    name: str
    confidence: float
    is_hinglish: bool = False


def normalize_indic_numerals(text: str) -> str:
    """Converts numerals across all major Indic scripts into standard ASCII digits (0-9)."""
    if not text:
        return ""
    result = text
    for digit_map in INDIC_DIGIT_MAPS.values():
        result = result.translate(digit_map)
    return result


def normalize_unicode_text(text: str) -> str:
    """
    Applies comprehensive Unicode NFKC normalization, strips zero-width spaces,
    normalizes Nukta combinations in Indic scripts, and cleans whitespace.
    """
    if not text:
        return ""

    # 1. NFKC Canonical Decomposition & Composition
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Strip Zero-Width and invisible control characters
    normalized = re.sub(r"[\u200B-\u200D\uFEFF\u200E\u200F]", "", normalized)

    # 3. Translate Indic numerals to ASCII digits
    normalized = normalize_indic_numerals(normalized)

    # 4. Devanagari Nukta / Spelling unification to standard forms
    normalized = normalized.replace("\u095c", "\u0921\u093c")  # ड़ -> ड़
    normalized = normalized.replace("\u095d", "\u0922\u093c")  # ढ़ -> ढ़
    normalized = normalized.replace("\u095b", "\u091c\u093c")  # ज़ -> ज़
    normalized = normalized.replace("\u0959", "\u0916\u093c")  # ख़ -> ख़
    normalized = re.sub(r"\u093c+", "\u093c", normalized)  # Deduplicate consecutive nuktas
    normalized = re.sub(r"\bकरोड\b(?!\u093c)", "करोड़", normalized)
    normalized = normalized.replace("लाख़", "लाख")
    normalized = normalized.replace("हज़ार", "हजार")
    normalized = normalized.replace("रू.", "₹")
    normalized = normalized.replace("रू", "रु")
    normalized = normalized.replace("ರೂ.", "₹")

    # 5. Collapse excessive whitespace
    normalized = " ".join(normalized.split())

    return normalized


def detect_language_multilingual(text: str, hint_code: Optional[str] = None) -> LanguageInfo:
    """
    Deterministically detects the language of the transcript using Unicode script analysis,
    lexical markers for Devanagari disambiguation (Hindi vs Marathi), Hinglish detection,
    and STT hint integration.
    """
    if not text or not text.strip():
        clean_hint = (hint_code or "en").strip().lower().split("-")[0]
        meta = LANGUAGE_METADATA.get(clean_hint, LANGUAGE_METADATA["en"])
        return LanguageInfo(
            code=clean_hint if clean_hint in LANGUAGE_METADATA else "en",
            locale=meta["locale"],
            name=meta["name"],
            confidence=0.50,
            is_hinglish=False
        )

    clean = normalize_unicode_text(text)
    lower = clean.lower()

    # Script character distribution
    script_counts = {
        "kannada": len(re.findall(r"[\u0C80-\u0CFF]", clean)),
        "devanagari": len(re.findall(r"[\u0900-\u097F]", clean)),
        "tamil": len(re.findall(r"[\u0B80-\u0BFF]", clean)),
        "telugu": len(re.findall(r"[\u0C00-\u0C7F]", clean)),
        "bengali": len(re.findall(r"[\u0980-\u09FF]", clean)),
        "gujarati": len(re.findall(r"[\u0A80-\u0AFF]", clean)),
        "malayalam": len(re.findall(r"[\u0D00-\u0D7F]", clean)),
        "gurmukhi": len(re.findall(r"[\u0A00-\u0A7F]", clean)),
        "odia": len(re.findall(r"[\u0B00-\u0B7F]", clean)),
        "latin": len(re.findall(r"[a-zA-Z]", clean)),
    }

    total_indic = sum(v for k, v in script_counts.items() if k != "latin")
    latin_count = script_counts["latin"]

    # Check for Hinglish
    if latin_count > 0 and latin_count >= total_indic:
        words = set(re.findall(r"[a-z]+", lower))
        hinglish_hits = len(words.intersection(HINGLISH_LEXICAL_MARKERS))
        if hinglish_hits >= 2 or (hinglish_hits >= 1 and any(w in words for w in ["mera", "mujhe", "kholna", "rupaye", "budget"])):
            return LanguageInfo(
                code="hi",
                locale="hi-IN",
                name="Hindi (Hinglish)",
                confidence=0.92,
                is_hinglish=True
            )

    clean_hint = (hint_code or "").strip().lower().split("-")[0]
    if clean_hint in ["kn", "kannada"] and script_counts["kannada"] > 0:
        return LanguageInfo(code="kn", locale="kn-IN", name="Kannada", confidence=0.98)
    if clean_hint in ["ta", "tamil"] and script_counts["tamil"] > 0:
        return LanguageInfo(code="ta", locale="ta-IN", name="Tamil", confidence=0.98)
    if clean_hint in ["te", "telugu"] and script_counts["telugu"] > 0:
        return LanguageInfo(code="te", locale="te-IN", name="Telugu", confidence=0.98)

    dominant_script, count = max(script_counts.items(), key=lambda x: x[1])

    if count == 0:
        meta = LANGUAGE_METADATA.get(clean_hint, LANGUAGE_METADATA["en"])
        return LanguageInfo(
            code=clean_hint if clean_hint in LANGUAGE_METADATA else "en",
            locale=meta["locale"],
            name=meta["name"],
            confidence=0.50
        )

    if dominant_script == "kannada":
        return LanguageInfo(code="kn", locale="kn-IN", name="Kannada", confidence=0.98)
    elif dominant_script == "tamil":
        return LanguageInfo(code="ta", locale="ta-IN", name="Tamil", confidence=0.98)
    elif dominant_script == "telugu":
        return LanguageInfo(code="te", locale="te-IN", name="Telugu", confidence=0.98)
    elif dominant_script == "bengali":
        return LanguageInfo(code="bn", locale="bn-IN", name="Bengali", confidence=0.98)
    elif dominant_script == "gujarati":
        return LanguageInfo(code="gu", locale="gu-IN", name="Gujarati", confidence=0.98)
    elif dominant_script == "malayalam":
        return LanguageInfo(code="ml", locale="ml-IN", name="Malayalam", confidence=0.98)
    elif dominant_script == "gurmukhi":
        return LanguageInfo(code="pa", locale="pa-IN", name="Punjabi", confidence=0.98)
    elif dominant_script == "odia":
        return LanguageInfo(code="or", locale="or-IN", name="Odia", confidence=0.98)
    elif dominant_script == "devanagari":
        words = set(re.findall(r"[\u0900-\u097F]+", clean))
        marathi_hits = len(words.intersection(MARATHI_LEXICAL_MARKERS))
        hindi_hits = len(words.intersection(HINDI_LEXICAL_MARKERS))

        if "\u0933" in clean or (marathi_hits > hindi_hits and marathi_hits > 0) or (clean_hint == "mr" and marathi_hits >= hindi_hits):
            return LanguageInfo(code="mr", locale="mr-IN", name="Marathi", confidence=0.95)
        return LanguageInfo(code="hi", locale="hi-IN", name="Hindi", confidence=0.96)
    else:
        if clean_hint in LANGUAGE_METADATA and clean_hint != "en":
            meta = LANGUAGE_METADATA[clean_hint]
            return LanguageInfo(
                code=clean_hint,
                locale=meta["locale"],
                name=meta["name"],
                confidence=0.85,
                is_hinglish=(clean_hint == "hi")
            )
        return LanguageInfo(code="en", locale="en-IN", name="English", confidence=0.95)
