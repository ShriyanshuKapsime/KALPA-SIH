import re
from typing import Tuple

# ISO 639-1 code to full display name mapping
LANGUAGE_MAP = {
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "od": "Odia",
    "ur": "Urdu",
}

# Distinctive word lists for Devanagari discrimination (Hindi vs Marathi)
MARATHI_MARKERS = {
    "माझ्या", "गावात", "आहे", "करायचा", "दुकानाचा", "पाहिಜೆ", "सुरू", "व्यवसाय",
    "आम्ही", "करतो", "आहेत", "चालू", "करावा", "सांगा", "माझे", "करायचे", "इच्छितो",
    "दुकान", "भांडवल", "रुपये", "पैसे", "आहेत", "होते", "शिलाई", "शेती"
}

HINDI_MARKERS = {
    "मुझे", "अपने", "गांव", "गाँव", "में", "दुकान", "शुरू", "करनी", "है", "मेरे",
    "पास", "रुपये", "रुपए", "चाहता", "हूँ", "हूं", "करना", "चाहती", "कारोबार",
    "खोलना", "व्यापार", "लाख", "हजार", "करोड़", "खेती", "सिलाई", "अनुभव"
}

KANNADA_MARKERS = {
    "ನಾನು", "ನನ್ನ", "ಹಳ್ಳಿಯಲ್ಲಿ", "ಊರಿನಲ್ಲಿ", "ಪ್ರಾರಂಭಿಸಲು", "ಆರಂಭಿಸಲು", "ಬಯಸುತ್ತೇನೆ",
    "ಮಾಡಬೇಕು", "ಇದೆ", "ಲಕ್ಷ", "ಸಾವಿರ", "ಅನುಭವ", "ಕೃಷಿ", "ಡೈರಿ", "ಅಂಗಡಿ"
}


def detect_language(text: str, override_code: str = None) -> Tuple[str, str]:
    """
    Deterministically detects language code and human-readable name for given text.
    Handles Indic Unicode blocks with priority:
    1. English
    2. Kannada
    3. Hindi
    Then other Indian languages (Marathi, Tamil, Telugu, etc.).
    """
    if override_code and override_code in LANGUAGE_MAP:
        return override_code, LANGUAGE_MAP[override_code]

    if not text or not text.strip():
        return "en", "English"

    clean_text = text.strip()

    # Check for specific Indic scripts by Unicode range
    script_counts = {
        "kannada": len(re.findall(r"[\u0C80-\u0CFF]", clean_text)),
        "devanagari": len(re.findall(r"[\u0900-\u097F]", clean_text)),
        "tamil": len(re.findall(r"[\u0B80-\u0BFF]", clean_text)),
        "telugu": len(re.findall(r"[\u0C00-\u0C7F]", clean_text)),
        "bengali": len(re.findall(r"[\u0980-\u09FF]", clean_text)),
        "gujarati": len(re.findall(r"[\u0A80-\u0AFF]", clean_text)),
        "malayalam": len(re.findall(r"[\u0D00-\u0D7F]", clean_text)),
        "gurmukhi": len(re.findall(r"[\u0A00-\u0A7F]", clean_text)),
        "odia": len(re.findall(r"[\u0B00-\u0B7F]", clean_text)),
        "latin": len(re.findall(r"[a-zA-Z]", clean_text)),
    }

    # If Kannada script has any meaningful presence, prioritize Kannada
    if script_counts["kannada"] > 0 and script_counts["kannada"] >= (script_counts["latin"] * 0.3):
        return "kn", "Kannada"

    # Find dominant script
    dominant_script, count = max(script_counts.items(), key=lambda x: x[1])

    if count == 0:
        return "en", "English"

    if dominant_script == "kannada":
        return "kn", "Kannada"
    elif dominant_script == "tamil":
        return "ta", "Tamil"
    elif dominant_script == "telugu":
        return "te", "Telugu"
    elif dominant_script == "bengali":
        return "bn", "Bengali"
    elif dominant_script == "gujarati":
        return "gu", "Gujarati"
    elif dominant_script == "malayalam":
        return "ml", "Malayalam"
    elif dominant_script == "gurmukhi":
        return "pa", "Punjabi"
    elif dominant_script == "odia":
        return "or", "Odia"
    elif dominant_script == "devanagari":
        # Disambiguate Hindi vs Marathi
        words = set(re.findall(r"[\u0900-\u097F]+", clean_text))
        marathi_hits = len(words.intersection(MARATHI_MARKERS))
        hindi_hits = len(words.intersection(HINDI_MARKERS))

        # Check for Marathi distinctive characters (e.g. ळ \u0933)
        if "\u0933" in clean_text or (marathi_hits > hindi_hits and marathi_hits > 0) or any(w in clean_text for w in ["माझ्या", "गावात", "इच्छितो", "चालू करायचा"]):
            return "mr", "Marathi"
        return "hi", "Hindi"
    else:
        return "en", "English"
