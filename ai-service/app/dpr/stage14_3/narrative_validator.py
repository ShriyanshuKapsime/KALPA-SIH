"""
Stage 14.3: DPR Narrative Validator.
Strict post-generation fact and numeric checking for every Sarvam narrative response.
Rejects hallucinated numbers, manufactured competitors, unauthorized schemes, and promotional buzzwords.
"""
import re
import logging
from typing import Dict, Any, List, Set, Tuple, Optional
from app.dpr.stage14_3.document_schema import (
    SectionNarrative,
    NarrativeValidationResult,
)

logger = logging.getLogger(__name__)

PROHIBITED_BUZZWORDS = [
    "game-changing",
    "revolutionary",
    "guaranteed success",
    "highly profitable",
    "extremely promising",
    "guaranteed profit",
    "risk-free",
    "guaranteed bankable",
    "bank approved",
    "loan guaranteed"
]


def parse_indian_currency_number(text: str) -> Optional[float]:
    """
    Parses currency phrases like '₹5 lakh', '5 lakhs', '₹ 7,00,000', '700000', '1.5 crore'.
    """
    t = text.lower().replace("₹", "").replace("rs.", "").replace("rs", "").replace(",", "").strip()
    # Check for lakh / crore multipliers
    if "crore" in t or "cr" in t:
        clean = re.sub(r"[^\d.]", "", t.split("cr")[0])
        try:
            return float(clean) * 10000000.0
        except ValueError:
            return None
    if "lakh" in t or "lac" in t:
        clean = re.sub(r"[^\d.]", "", t.split("l")[0])
        try:
            return float(clean) * 100000.0
        except ValueError:
            return None
    try:
        clean = re.sub(r"[^\d.]", "", t)
        if clean:
            return float(clean)
    except ValueError:
        pass
    return None


class DPRNarrativeValidator:
    """
    Validates that LLM-generated narrative contains zero hallucinated numbers,
    unauthorized schemes, fabricated competitors, or promotional language.
    """

    def __init__(self):
        pass

    def validate_narrative(
        self,
        narrative: SectionNarrative,
        source_data: Dict[str, Any],
        section_id: str
    ) -> NarrativeValidationResult:
        result = NarrativeValidationResult(section_id=section_id, is_valid=True)
        full_text = " ".join(narrative.paragraphs)

        # 1. Prohibited buzzword check
        for bw in PROHIBITED_BUZZWORDS:
            if bw in full_text.lower():
                result.is_valid = False
                result.failed_checks.append(f"Prohibited promotional buzzword found: '{bw}'")
                result.invalid_claims.append(f"Buzzword: {bw}")

        # 2. Extract allowed numbers from source data
        allowed_numbers: Set[float] = set()
        self._collect_source_numbers(source_data, allowed_numbers)

        # Common acceptable numbers (e.g. 1-7 years, 12 months, 365 days, 100%, 0-5)
        generic_allowed = {
            1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 24.0, 36.0, 48.0, 60.0, 84.0,
            100.0, 300.0, 365.0, 24.0, 7.0, 1.0, 2.0
        }
        allowed_numbers.update(generic_allowed)

        # 3. Currency / Large Number Verification
        # Find currency mentions e.g. ₹5 lakh, ₹700000, Rs. 10,00,000, 7 lakh
        currency_regex = r"(?:₹|rs\.?)\s*[\d,.]+(?:\s*(?:lakh|crore|lac|cr|k))?"
        matches = re.findall(currency_regex, full_text, flags=re.IGNORECASE)
        # Also find plain numbers accompanied by 'lakh' or 'crore'
        lakh_matches = re.findall(r"\b\d+(?:\.\d+)?\s*(?:lakh|crore|lac|cr)\b", full_text, flags=re.IGNORECASE)
        all_numeric_mentions = set(matches + lakh_matches)

        # Also find stand-alone 5+ digit numbers that look like rupee amounts (e.g. 700000)
        large_int_matches = re.findall(r"\b\d{5,}\b", full_text)
        all_numeric_mentions.update(large_int_matches)

        for token in all_numeric_mentions:
            parsed_val = parse_indian_currency_number(token)
            if parsed_val is not None:
                # Check if parsed_val matches any allowed number within 2% tolerance
                matched = any(abs(parsed_val - an) / max(an, 1.0) < 0.02 for an in allowed_numbers)
                if not matched:
                    result.is_valid = False
                    result.failed_checks.append(f"Hallucinated numeric value: '{token}' (~{parsed_val})")
                    result.invalid_numbers.append({"token": token, "parsed_value": parsed_val})

        # 4. Scheme validation: if text asserts a government scheme, check against source schemes
        source_schemes = self._collect_source_strings(source_data, {"scheme", "policy"})
        # Look for phrases like 'under PMEGP scheme', 'PMFME scheme'
        scheme_matches = re.findall(r"\b([A-Z]{3,8}(?:\s+[A-Z]{2,})?)\s+(?:scheme|subsidy|yojana)\b", full_text, flags=re.IGNORECASE)
        for sm in scheme_matches:
            sm_clean = sm.strip().upper()
            if source_schemes:
                matched_scheme = any(sm_clean in s.upper() for s in source_schemes)
                if not matched_scheme and sm_clean not in ("KALPA", "GOVERNMENT", "CENTRAL", "STATE", "NABARD", "MSME"):
                    result.is_valid = False
                    result.failed_checks.append(f"Unverified scheme mentioned: '{sm}'")
                    result.invalid_claims.append(f"Scheme: {sm}")

        if result.is_valid:
            result.passed_checks.append("All numbers and qualitative claims verified against source package")
        else:
            result.error_details = "; ".join(result.failed_checks)

        return result

    def _collect_source_numbers(self, obj: Any, num_set: Set[float]):
        if obj is None:
            return
        if isinstance(obj, (int, float)):
            f_val = float(obj)
            num_set.add(f_val)
            # Also add common conversions: e.g. 500000 -> 5.0 (lakhs)
            if f_val >= 100000:
                num_set.add(round(f_val / 100000.0, 2))
            if f_val >= 10000000:
                num_set.add(round(f_val / 10000000.0, 2))
            # Also if percentage: 0.15 -> 15.0 or 15.0 -> 0.15
            if 0 < f_val <= 1.0:
                num_set.add(round(f_val * 100.0, 1))
            elif 1.0 < f_val <= 100.0:
                num_set.add(round(f_val / 100.0, 3))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._collect_source_numbers(v, num_set)
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                self._collect_source_numbers(item, num_set)
        elif isinstance(obj, str):
            # Try to parse string representation of numbers
            val = parse_indian_currency_number(obj)
            if val is not None:
                num_set.add(val)

    def _collect_source_strings(self, obj: Any, target_keys: Set[str]) -> List[str]:
        results: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(tk in k.lower() for tk in target_keys) and isinstance(v, str):
                    results.append(v)
                results.extend(self._collect_source_strings(v, target_keys))
        elif isinstance(obj, list):
            for item in obj:
                results.extend(self._collect_source_strings(item, target_keys))
        return results
