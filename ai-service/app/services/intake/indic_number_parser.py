"""
Compositional Indic Number Parser.
Supports Hindi, Kannada, Marathi, Tamil, Telugu, English, and Hinglish.
Parses multi-tier compound scales (Crores + Lakhs + Thousands + Hundreds + Units + Fractions),
compact notations (1.5L, 2cr, 50k), and formatted numerals (₹1,00,000, 100000).
"""

import re
import unicodedata
from typing import Optional, Tuple, List, Dict, Any
from app.services.intake.language_normalizer import normalize_unicode_text

# 1. Base Words (0 - 99)
_RAW_BASE_WORDS: Dict[str, float] = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "twenty-one": 21, "twenty-two": 22, "twenty-three": 23, "twenty-four": 24, "twenty-five": 25,
    "thirty": 30, "thirty-five": 35, "forty": 40, "forty-five": 45, "fifty": 50, "fifty-five": 55,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,

    # Hinglish
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5, "chhah": 6, "chhe": 6, "chhey": 6,
    "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20, "ikkees": 21, "baees": 22, "teees": 23, "chaubees": 24,
    "pacchees": 25, "pachees": 25, "chhabbees": 26, "sattaees": 27, "atthaees": 28, "untees": 29,
    "tees": 30, "paintees": 35, "chalis": 40, "chalees": 40, "paintalis": 45, "pachaas": 50, "pachas": 50,
    "saath": 60, "sath": 60, "sattar": 70, "assi": 80, "nabbe": 90, "nabbey": 90,

    # Hindi
    "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25, "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29,
    "तीस": 30, "इकतीस": 31, "बत्तीस": 32, "तैंतीस": 33, "चौंतीस": 34, "पैंतीस": 35, "छत्तीस": 36, "सैंतीस": 37, "अड़तीस": 38, "उनतालीस": 39,
    "चालीस": 40, "इकतालीस": 41, "बयालीस": 42, "तैंतालीस": 43, "चवालीस": 44, "पैंतालीस": 45, "छियालीस": 46, "सैंतालीस": 47, "अड़तालीस": 48, "उनचास": 49,
    "पचास": 50, "इक्यावन": 51, "बावन": 52, "तिरेपन": 53, "चौवन": 54, "पचपन": 55, "छप्पन": 56, "सत्तावन": 57, "अट्ठावन": 58, "उनसठ": 59,
    "साठ": 60, "इकसठ": 61, "बासठ": 62, "तिरसठ": 63, "चौंसठ": 64, "पैंसठ": 65, "छियासठ": 66, "सरसठ": 67, "अड़सठ": 68, "उनहत्तर": 69,
    "सत्तर": 70, "इकहत्तर": 71, "बहत्तर": 72, "तिहत्तर": 73, "चौहत्तर": 74, "पचहत्तर": 75, "छिहत्तर": 76, "सतहत्तर": 77, "अठहत्तर": 78, "उन्नासी": 79,
    "अस्सी": 80, "इक्यासी": 81, "बयासी": 82, "तिरासी": 83, "चौरासी": 84, "पचासी": 85, "छियासी": 86, "सत्तासी": 87, "अट्ठासी": 88, "नवासी": 89,
    "नब्बे": 90, "इक्यानवे": 91, "बानवे": 92, "तिरानवे": 93, "चौरानवे": 94, "पंचानवे": 95, "छियानवे": 96, "सत्तानवे": 97, "अट्ठानवे": 98, "निन्यानवे": 99,

    # Marathi
    "दोन": 2, "पाच": 5, "सहा": 6, "दहा": 10, "अकरा": 11, "बारा": 12, "तेरा": 13, "चौदा": 14, "पंधरा": 15, "सोळा": 16, "सतरा": 17,
    "अठरा": 18, "एकोणीस": 19, "वीस": 20, "पंचवीस": 25, "चाळीस": 40, "पन्नास": 50, "ऐंशी": 80, "नव्वद": 90,

    # Kannada
    "ಸೊನ್ನೆ": 0, "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10,
    "ಹನ್ನೊಂದು": 11, "ಹನ್ನೆರಡು": 12, "ಹದಿಮೂರು": 13, "ಹದಿನಾಲ್ಕು": 14, "ಹದಿನೈದು": 15, "ಹದಿನಾರು": 16, "ಹದಿನೇಳು": 17, "ಹದಿನೆಂಟು": 18, "ಹತ್ತೊಂಬತ್ತು": 19,
    "ಇಪ್ಪತ್ತು": 20, "ಇಪ್ಪತ್ತೈದು": 25, "ಮೂವತ್ತು": 30, "ಮೂವತ್ತೈದು": 35, "ನಲವತ್ತು": 40, "ನಲವತ್ತೈದು": 45, "ಐವತ್ತು": 50, "ಐವತ್ತೈದು": 55,
    "ಅರವತ್ತು": 60, "ಎಪ್ಪತ್ತು": 70, "ಎಂಬತ್ತು": 80, "ತೊಂಬತ್ತು": 90,

    # Tamil
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6, "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10,
    "இருபது": 20, "இருபத்தைந்து": 25, "முப்பது": 30, "நாற்பது": 40, "ஐம்பது": 50, "அறுபது": 60, "எழுபது": 70, "எண்பது": 80, "தொண்ணூறு": 90,

    # Telugu
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "ఆరు": 6, "ఏడు": 7, "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10,
    "ఇరవై": 20, "ఇరవైఐదు": 25, "ముప్పై": 30, "నలభై": 40, "యాభై": 50, "అరవై": 60, "డెబ్బై": 70, "ఎనభై": 80, "తొంభై": 90,
}

# 2. Standalone Fractions & Modifiers
_RAW_FRACTION_STANDALONE: Dict[str, float] = {
    # Standalone values
    "आधा": 0.5, "aadha": 0.5, "adha": 0.5, "half": 0.5, "अर्धा": 0.5,
    "डेढ़": 1.5, "डेढ़": 1.5, "dedh": 1.5, "dehd": 1.5, "दीड": 1.5, "ಒಂದೂವರೆ": 1.5, "ஒன்றரை": 1.5, "ఒకటిన్నర": 1.5,
    "ढाई": 2.5, "dhai": 2.5, "dhaai": 2.5, "अडीच": 2.5, "ಎರಡುವರೆ": 2.5, "இரண்டரை": 2.5, "రెండున్నర": 2.5,
    "सवा": 1.25, "sava": 1.25, "sawah": 1.25, "सव्वा": 1.25,
    "पौन": 0.75, "पौने": 0.75, "paun": 0.75, "paune": 0.75, "पाऊण": 0.75,
}

# 3. Scale Multipliers
_RAW_SCALES: Dict[str, int] = {
    # Crores (10,000,000)
    "करोड़": 10000000, "करोड़": 10000000, "करोड": 10000000, "कोटी": 10000000, "ಕೋಟಿ": 10000000, "ಕೋಟಿಗಳು": 10000000,
    "கோடி": 10000000, "కోటి": 10000000, "crore": 10000000, "crores": 10000000, "cr": 10000000, "karod": 10000000,
    "करोड": 10000000, "करोड़": 10000000, "\u0915\u0930\u094b\u0921\u093c": 10000000, "\u0915\u0930\u094b\u095c": 10000000,

    # Lakhs (100,000)
    "लाख": 100000, "लाख़": 100000, "लाक": 100000, "लक्षांत": 100000, "ಲಕ್ಷ": 100000, "ಲಕ್ಷಗಳು": 100000,
    "லட்சம்": 100000, "లక్ష": 100000, "లక్షలు": 100000, "lakh": 100000, "lakhs": 100000, "lac": 100000, "lacs": 100000, "l": 100000,

    # Thousands (1,000)
    "हजार": 1000, "हज़ार": 1000, "ಸಾವಿರ": 1000, "ಸಾವಿರಾರು": 1000, "ஆயிரம்": 1000, "வேయి": 1000, "వేలు": 1000,
    "thousand": 1000, "thousands": 1000, "k": 1000, "hazar": 1000, "hazaar": 1000,

    # Hundreds (100)
    "सौ": 100, "सैंकड़ा": 100, "ನೂರು": 100, "ಶಂभर": 100, "शे": 100, "நூறு": 100, "వంద": 100,
    "hundred": 100, "hundreds": 100, "sau": 100,
}


def _build_normalized_map(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    norm_dict = {}
    for k, v in raw_dict.items():
        k_lower = k.lower()
        norm_dict[k_lower] = v
        norm_dict[normalize_unicode_text(k_lower)] = v
        norm_dict[unicodedata.normalize("NFC", k_lower)] = v
        norm_dict[unicodedata.normalize("NFD", k_lower)] = v
        norm_dict[unicodedata.normalize("NFKC", k_lower)] = v
        norm_dict[unicodedata.normalize("NFKD", k_lower)] = v
        # Alternate nukta character mapping
        norm_dict[k_lower.replace("\u095c", "\u0921\u093c")] = v
        norm_dict[k_lower.replace("\u0921\u093c", "\u095c")] = v
        norm_dict[k_lower.replace("\u095d", "\u0922\u093c")] = v
        norm_dict[k_lower.replace("\u0922\u093c", "\u095d")] = v
    return norm_dict


BASE_WORDS = _build_normalized_map(_RAW_BASE_WORDS)
FRACTION_STANDALONE = _build_normalized_map(_RAW_FRACTION_STANDALONE)
SCALES = _build_normalized_map(_RAW_SCALES)


def parse_fractional_compound(phrase: str) -> Optional[float]:
    clean_p = normalize_unicode_text(phrase).strip()
    clean_p = re.sub(r"[₹\u20B9$,\-।!?\(\)]", " ", clean_p)
    tokens = clean_p.split()
    if not tokens:
        return None

    if len(tokens) == 1:
        tok = tokens[0]
        return FRACTION_STANDALONE.get(tok)

    if len(tokens) == 2:
        prefix, base_tok = tokens[0], tokens[1]
        base_val = BASE_WORDS.get(base_tok)
        if base_val is None:
            try:
                base_val = float(base_tok)
            except ValueError:
                return None

        # साढ़े / sadhe / साडे (+0.5)
        if prefix in ["साढ़े", "साढ़े", "साडे", "sadhe", "saade", normalize_unicode_text("साढ़े")]:
            return base_val + 0.5

        # सवा / sava / सव्वा (+0.25)
        if prefix in ["सवा", "सव्वा", "sava", "sawah", normalize_unicode_text("सवा")]:
            return base_val + 0.25

        # पौने / paune (-0.25)
        if prefix in ["पौने", "paune", "पाऊण", normalize_unicode_text("पौने")]:
            return base_val - 0.25

    return None


def parse_compositional_indic_number(text: str) -> Optional[int]:
    """
    Compositional parser that evaluates multi-tier Indian and English number expressions.
    """
    if not text:
        return None

    clean = normalize_unicode_text(text).lower()
    clean = re.sub(r"[₹\u20B9$,\-।!?\(\)]", " ", clean)
    clean = re.sub(r"(?:^|[^\w])(?:rs\.?|inr|रू\.?|ರೂ\.?)(?:[^\w]|$)", " ", clean, flags=re.IGNORECASE)
    tokens = clean.split()

    total = 0.0
    i = 0
    matched_any_scale = False

    while i < len(tokens):
        matched_chunk = False

        for span_len in [4, 3, 2, 1]:
            if i + span_len <= len(tokens):
                last_token = tokens[i + span_len - 1]
                scale_mult = SCALES.get(last_token)

                if scale_mult is not None:
                    prefix_tokens = tokens[i : i + span_len - 1]

                    if not prefix_tokens:
                        total += scale_mult
                        matched_chunk = True
                        matched_any_scale = True
                        i += span_len
                        break

                    prefix_str = " ".join(prefix_tokens)
                    frac_val = parse_fractional_compound(prefix_str)
                    if frac_val is not None:
                        total += frac_val * scale_mult
                        matched_chunk = True
                        matched_any_scale = True
                        i += span_len
                        break

                    base_val = BASE_WORDS.get(prefix_str)
                    if base_val is not None:
                        total += base_val * scale_mult
                        matched_chunk = True
                        matched_any_scale = True
                        i += span_len
                        break

                    try:
                        num_val = float(prefix_str)
                        total += num_val * scale_mult
                        matched_chunk = True
                        matched_any_scale = True
                        i += span_len
                        break
                    except ValueError:
                        pass

                    if prefix_str in ["one hundred", "एक सौ", "100"]:
                        total += 100 * scale_mult
                        matched_chunk = True
                        matched_any_scale = True
                        i += span_len
                        break

        if not matched_chunk:
            tok = tokens[i]
            if tok in BASE_WORDS and matched_any_scale:
                total += BASE_WORDS[tok]
            i += 1

    if matched_any_scale and total > 0:
        return int(total)

    return None


def parse_indic_number_expression(text: str) -> Optional[int]:
    """
    Main entrypoint for parsing any Indian number expression.
    """
    if not text:
        return None

    clean = normalize_unicode_text(text).lower()

    # 1. Compositional parser
    comp_val = parse_compositional_indic_number(clean)
    if comp_val is not None and comp_val > 0:
        return comp_val

    # 2. Compact scale regex matching
    scale_names = sorted(set(SCALES.keys()), key=lambda x: len(x), reverse=True)
    scale_pattern = "|".join(re.escape(k) for k in scale_names)

    compact_match = re.search(rf"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*({scale_pattern})(?!\w)", clean, re.IGNORECASE)
    if compact_match:
        try:
            val = float(compact_match.group(1))
            unit = compact_match.group(2)
            multiplier = SCALES.get(unit, 1)
            return int(val * multiplier)
        except (ValueError, KeyError):
            pass

    # 3. Standard Formatted Integer (e.g. "₹1,00,000", "50,000", "100000")
    digits_only = re.sub(r"[,\s]", "", clean)
    raw_num_match = re.search(r"(?:₹|rs\.?|inr)?\s*([1-9]\d{3,9})", digits_only, re.IGNORECASE)
    if raw_num_match:
        try:
            return int(raw_num_match.group(1))
        except ValueError:
            pass

    return None
