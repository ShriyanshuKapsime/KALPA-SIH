"""
Deterministic Indian Currency & Monetary Amount Normalization Layer.
Parses Hindi, Indic, and Indian English monetary expressions into standard numeric amounts (INR).
Zero LLM hallucination - purely deterministic token resolution and grammar parsing.

Supports:
- "एक लाख" -> 100000
- "एक लाख रुपये" -> 100000
- "डेढ़ लाख" / "डेढ लाख" -> 150000
- "ढाई लाख" -> 250000
- "साढ़े तीन लाख" -> 350000
- "दो लाख पचास हजार" -> 250000
- "पचास हजार" -> 50000
- "एक करोड़" -> 10000000
- "1.5 lakh" / "1.5 लाख" -> 150000
- "₹1 लाख" / "1 लाख" -> 100000
- "10 लाख" -> 1000000
- "75 हजार" -> 75000
"""
import re
from typing import Optional, Union

# Number words mapping (Hindi / English)
HINDI_NUMBER_WORDS = {
    # 0 - 9
    "शून्य": 0, "ज़ीरो": 0, "जीरो": 0, "zero": 0,
    "एक": 1, "one": 1,
    "दो": 2, "two": 2,
    "तीन": 3, "three": 3,
    "चार": 4, "four": 4,
    "पांच": 5, "पाँच": 5, "five": 5,
    "छह": 6, "छः": 6, "छ": 6, "six": 6,
    "सात": 7, "seven": 7,
    "आठ": 8, "eight": 8,
    "नौ": 9, "nine": 9,
    # 10 - 19
    "दस": 10, "ten": 10,
    "ग्यारह": 11, "eleven": 11,
    "बारह": 12, "twelve": 12,
    "तेरह": 13, "thirteen": 13,
    "चौदह": 14, "fourteen": 14,
    "पंद्रह": 15, "पन्द्रह": 15, "fifteen": 15,
    "सोलह": 16, "sixteen": 16,
    "सत्रह": 17, "seventeen": 17,
    "अठारह": 18, "eighteen": 18,
    "उन्नीस": 19, "nineteen": 19,
    # 20 - 29
    "बीस": 20, "twenty": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25,
    "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29,
    # 30 - 39
    "तीस": 30, "thirty": 30,
    "इकतीस": 31, "बत्तीस": 32, "तैंतीस": 33, "चौंतीस": 34, "पैंतीस": 35,
    "छत्तीस": 36, "सैंतीस": 37, "अड़तीस": 38, "उनतालीस": 39,
    # 40 - 49
    "चालीस": 40, "forty": 40,
    "इकतालीस": 41, "बयालीस": 42, "तैंतालीस": 43, "चवालीस": 44, "पैंतालीस": 45,
    "छियालीस": 46, "सैंतालीस": 47, "अड़तालीस": 48, "उनचास": 49,
    # 50 - 59
    "पचास": 50, "fifty": 50,
    "इक्यावन": 51, "बावन": 52, "तिरेपन": 53, "चौवन": 54, "पचपन": 55,
    "छप्पन": 56, "सत्तावन": 57, "अट्ठावन": 58, "उनसठ": 59,
    # 60 - 69
    "साठ": 60, "sixty": 60,
    "इकसठ": 61, "बासठ": 62, "तिरसठ": 63, "चौंसठ": 64, "पैंसठ": 65,
    "छियासठ": 66, "सरसठ": 67, "अड़सठ": 68, "उनहत्तर": 69,
    # 70 - 79
    "सत्तर": 70, "seventy": 70,
    "इकहत्तर": 71, "बहत्तर": 72, "तिहत्तर": 73, "चौहत्तर": 74, "पचहत्तर": 75,
    "छिहत्तर": 76, "सतहत्तर": 77, "अठहत्तर": 78, "उन्नासी": 79,
    # 80 - 89
    "अस्सी": 80, "eighty": 80,
    "इक्यासी": 81, "बयासी": 82, "तिरासी": 83, "चौरासी": 84, "पचासी": 85,
    "छियासी": 86, "सतासी": 87, "अट्ठासी": 88, "नवासी": 89,
    # 90 - 99
    "नब्बे": 90, "ninety": 90,
    "इक्यानवे": 91, "बानवे": 92, "तिरानवे": 93, "चौरानवे": 94, "पंचानवे": 95, "पिचानवे": 95,
    "छियानवे": 96, "सतानवे": 97, "अट्ठानवे": 98, "निन्यानवे": 99,
    # Hundred
    "सौ": 100, "hundred": 100,
}

# Special fractions
FRACTIONS = {
    "डेढ़": 1.5,
    "डेढ": 1.5,
    "ढाई": 2.5,
}

# Multiplier tokens
MULTIPLIERS = {
    # Crores
    "करोड़": 10000000,
    "करोड": 10000000,
    "cr": 10000000,
    "crore": 10000000,
    "crores": 10000000,
    # Lakhs
    "लाख": 100000,
    "लाखें": 100000,
    "lakh": 100000,
    "lakhs": 100000,
    "lac": 100000,
    "lacs": 100000,
    # Thousands
    "हजार": 1000,
    "हज़ार": 1000,
    "thousand": 1000,
    "thousands": 1000,
    "k": 1000,
    # Hundreds
    "सौ": 100,
    "hundred": 100,
}

IGNORE_WORDS = {
    "रुपये", "रुपया", "रुपए", "रु", "रू", "rupees", "rupee", "rs", "inr", "₹",
    "का", "की", "के", "लगभग", "करीब", "मात्र", "only", "around", "approx", "approximately"
}


def normalize_hindi_monetary_amount(text: Union[str, int, float, None]) -> Optional[float]:
    """
    Deterministically normalizes an Indian monetary string into a float value in INR.
    Returns None if text cannot be interpreted as a valid monetary amount.
    """
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)

    raw = str(text).strip()
    if not raw:
        return None

    # Clean punctuation except decimals and digits
    cleaned = raw.replace("₹", " ₹ ").replace(",", "").lower()

    # Direct numeric test (e.g. "500000" or "500000.0")
    try:
        val = float(cleaned)
        return val
    except ValueError:
        pass

    # Pattern: Digits + Multiplier (e.g. "1.5 lakh", "1.5 लाख", "10 lakh", "₹ 2.5 करोड़")
    m_num_mult = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(लाख|करोड़|करोड|हजार|हज़ार|सौ|lakh|lakhs|lac|lacs|crore|crores|cr|thousand|thousands|k)\b', cleaned, re.IGNORECASE)
    if m_num_mult:
        num_part = float(m_num_mult.group(1))
        unit_str = m_num_mult.group(2).lower()
        mult = MULTIPLIERS.get(unit_str, 1)
        # Check if followed by additional units like "दो लाख पचास हजार"
        remainder = cleaned[m_num_mult.end():].strip()
        rem_val = normalize_hindi_monetary_amount(remainder) if remainder else 0.0
        return (num_part * mult) + (rem_val or 0.0)

    # Token-based parsing for word numbers (e.g. "एक लाख", "डेढ़ लाख", "दो लाख पचास हजार")
    tokens = [t.strip() for t in re.split(r'[\s,]+', cleaned) if t.strip()]
    if not tokens:
        return None

    # Filter out currency terms and conversational stop words
    filt_tokens = [t for t in tokens if t not in IGNORE_WORDS]
    if not filt_tokens:
        return None

    total_amount = 0.0
    current_number = 0.0
    sawa_modifier = 0.0  # सवा (+0.25)
    sadhe_modifier = 0.0  # साढ़े (+0.5)
    paune_modifier = 0.0  # पौने (-0.25)

    recognized_any_num = False

    i = 0
    while i < len(filt_tokens):
        tok = filt_tokens[i]

        # Check special standalone fractions
        if tok in FRACTIONS:
            current_number = FRACTIONS[tok]
            recognized_any_num = True
            i += 1
            continue

        # Check modifiers
        if tok in ("साढ़े", "साढे"):
            sadhe_modifier = 0.5
            i += 1
            continue
        if tok in ("सवा",):
            sawa_modifier = 0.25
            i += 1
            continue
        if tok in ("पौने",):
            paune_modifier = -0.25
            i += 1
            continue

        # Check if digits
        if re.match(r'^[0-9]+(?:\.[0-9]+)?$', tok):
            current_number = float(tok)
            recognized_any_num = True
            i += 1
            continue

        # Check if number word
        if tok in HINDI_NUMBER_WORDS:
            base_val = HINDI_NUMBER_WORDS[tok]
            if sadhe_modifier:
                current_number = base_val + 0.5
                sadhe_modifier = 0.0
            elif sawa_modifier:
                current_number = base_val + 0.25
                sawa_modifier = 0.0
            elif paune_modifier:
                current_number = base_val - 0.25
                paune_modifier = 0.0
            else:
                current_number += base_val
            recognized_any_num = True
            i += 1
            continue

        # Check if multiplier
        if tok in MULTIPLIERS:
            mult = MULTIPLIERS[tok]
            if current_number == 0.0 and recognized_any_num is False:
                # e.g., "लाख" without prefix assumes 1
                current_number = 1.0
            total_amount += current_number * mult
            current_number = 0.0
            recognized_any_num = True
            i += 1
            continue

        # Unrecognized token in string
        i += 1

    total_amount += current_number

    if recognized_any_num and total_amount > 0:
        return float(total_amount)

    return None
