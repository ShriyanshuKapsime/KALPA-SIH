import re
from typing import Optional, Tuple

# Word to digit maps for English, Hindi, Kannada, and Marathi
NUMBER_WORDS = {
    # English
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
    # Hindi / Marathi
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20,
    "पच्चीस": 25, "तीस": 30, "पैंतीस": 35, "चालीस": 40, "पैंतालीस": 45, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    "सौ": 100, "दोन": 2, "पाच": 5, "दहा": 10,
    # Kannada
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10,
    "ಹನ್ನೊಂದು": 11, "ಹನ್ನೆರಡು": 12, "ಹದಿಮೂರು": 13, "ಹದಿನಾಲ್ಕು": 14, "ಹದಿನೈದು": 15, "ಹದಿನಾರು": 16, "ಹದಿನೇಳು": 17, "ಹದಿನೆಂಟು": 18, "ಹತ್ತೊಂಬತ್ತು": 19,
    "ಇಪ್ಪತ್ತು": 20, "ಇಪ್ಪತ್ತೈದು": 25, "ಮೂವತ್ತು": 30, "ಮೂವತ್ತೈದು": 35, "ನಲವತ್ತು": 40, "ನಲವತ್ತೈದು": 45, "ಐವತ್ತು": 50,
    "ಅರವತ್ತು": 60, "ಎಪ್ಪತ್ತು": 70, "ಎಂಬತ್ತು": 80, "ತೊಂಬತ್ತು": 90, "ನೂರು": 100
}

UNIT_MULTIPLIERS = {
    # English
    "k": 1000,
    "thousand": 1000,
    "thousands": 1000,
    "lac": 100000,
    "lacs": 100000,
    "lakh": 100000,
    "lakhs": 100000,
    "l": 100000,
    "cr": 10000000,
    "crore": 10000000,
    "crores": 10000000,
    # Hindi / Marathi
    "हजार": 1000,
    "हज़ार": 1000,
    "लाख": 100000,
    "करोड़": 10000000,
    "करोड": 10000000,
    "कोटी": 10000000,
    # Kannada
    "ಸಾವಿರ": 1000,
    "ಸಾವಿರಾರು": 1000,
    "ಲಕ್ಷ": 100000,
    "ಲಕ್ಷಗಳು": 100000,
    "ಕೋಟಿ": 10000000,
    "ಕೋಟಿಗಳು": 10000000,
}

KANNADA_DIGITS = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")
HINDI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_indic_digits(text: str) -> str:
    """Converts Kannada and Devanagari numerals to standard ASCII digits."""
    return text.translate(KANNADA_DIGITS).translate(HINDI_DIGITS)


def parse_indian_money(text: str) -> Tuple[Optional[int], str]:
    """
    Extracts and normalizes Indian currency expressions to integer amount in INR.
    Supports English, Kannada, Hindi, Marathi words, numbers, and abbreviations.
    Examples:
      - "₹2 lakh" -> 200000
      - "2 lakh rupees" -> 200000
      - "1.5 lakh" -> 150000
      - "₹50,000" -> 50000
      - "two lakhs" -> 200000
      - "ಎರಡು ಲಕ್ಷ" -> 200000
      - "2 ಲಕ್ಷ" -> 200000
      - "तीन लाख" -> 300000
      - "50 हजार" -> 50000
    """
    if not text or not text.strip():
        return None, "INR"

    currency = "INR"
    clean = normalize_indic_digits(text.lower())
    clean = clean.replace("₹", " ₹ ").replace("rs.", " rs ").replace("rs", " rs ")
    clean = clean.replace("rupees", " ").replace("rupee", " ").replace("रुपये", " ").replace("रुपए", " ")
    clean = clean.replace("ರೂಪಾಯಿ", " ").replace("ರೂಪಾಯಿಗಳು", " ").replace("ರೂ.", " ")

    # Case 1: Word-based numbers + unit e.g. "ಎರಡು ಲಕ್ಷ", "तीन लाख", "three lakh", "ಐವತ್ತು ಸಾವಿರ", "fifty thousand"
    word_num_keys = "|".join(re.escape(k) for k in NUMBER_WORDS.keys())
    unit_keys = "|".join(re.escape(k) for k in UNIT_MULTIPLIERS.keys())
    word_pattern = rf"({word_num_keys})\s*({unit_keys})"
    word_match = re.search(word_pattern, clean)
    if word_match:
        num_str = word_match.group(1)
        unit_str = word_match.group(2)
        base_val = NUMBER_WORDS.get(num_str, 0)
        mult_val = UNIT_MULTIPLIERS.get(unit_str, 1)
        if base_val > 0 and mult_val > 1:
            return int(base_val * mult_val), currency

    # Case 2: Numeric digit + unit e.g. "2 lakh", "2 ಲಕ್ಷ", "3.5 lakhs", "1.5 lakh", "50k", "50 ಸಾವಿರ", "3 लाख"
    num_unit_pattern = rf"(\d+(?:\.\d+)?)\s*({unit_keys})\b"
    num_unit_match = re.search(num_unit_pattern, clean)
    if num_unit_match:
        val = float(num_unit_match.group(1))
        unit = num_unit_match.group(2)
        multiplier = UNIT_MULTIPLIERS.get(unit, 1)
        return int(val * multiplier), currency

    # Case 3: Raw numbers with or without comma formatting e.g. "₹2,00,000", "50000", "200000"
    num_clean = re.sub(r"[,\s]", "", clean)
    raw_num_match = re.search(r"(?:₹|rs\.?|inr)?\s*([1-9]\d{3,9})", num_clean, re.IGNORECASE)
    if raw_num_match:
        try:
            return int(raw_num_match.group(1)), currency
        except ValueError:
            pass

    return None, currency
