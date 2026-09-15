"""
Canonical Multilingual Intake Extractor.
Orchestrates Language Normalization, Compositional Number Parsing, Contextual Amount Extraction,
Multilingual Business Concept Matching, Resilient LLM Refinement, and Validation with Provenance.
"""

import json
from dataclasses import asdict
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.llm_client import llm_client
from app.services.intake.language_normalizer import (
    LanguageInfo,
    normalize_unicode_text,
    detect_language_multilingual
)
from app.services.intake.amount_parser import parse_canonical_amount, AmountResult
from app.services.intake.business_entity_extractor import (
    extract_multilingual_business_entities,
    BusinessEntityResult
)


class CanonicalIntakeExtractor:
    """
    Main extraction engine for Stage 1 Intake.
    Guarantees deterministic correctness, zero reliance on external LLM availability,
    and strict data types (numeric capital in INR).
    """

    async def extract_canonical_profile(
        self,
        text: str,
        language_hint: Optional[str] = None,
        use_llm_refinement: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the full pipeline:
        1. Unicode normalization
        2. Language detection (Indic + English + Hinglish)
        3. Compositional amount parsing with provenance
        4. Business concept, intent, location, and skills extraction
        5. Resilient LLM refinement (if configured and enabled)
        6. Validation and canonical structured merge
        """
        if not text or not text.strip():
            lang_info = detect_language_multilingual("", hint_code=language_hint)
            return self._build_empty_profile(lang_info)

        # 1. Unicode & Script Normalization
        clean_text = normalize_unicode_text(text)

        # 2. Language Detection
        lang_info = detect_language_multilingual(clean_text, hint_code=language_hint)

        # 3. Canonical Amount & Financial Parsing
        amount_res: AmountResult = parse_canonical_amount(clean_text, language_code=lang_info.code)

        # 4. Business Concept, Intent, Location, Skills Parsing
        biz_res: BusinessEntityResult = extract_multilingual_business_entities(clean_text, language_code=lang_info.code)

        # 5. Build Baseline Deterministic Profile
        deterministic_profile = {
            "business_concept": biz_res.business_concept,
            "business_category_hint": biz_res.business_category_hint,
            "intent": biz_res.intent,
            "business_stage": biz_res.business_stage,
            "available_capital": amount_res.available_capital,
            "capital_currency": amount_res.currency,
            "currency_source": amount_res.currency_source,
            "loan_requested": amount_res.loan_requested,
            "proposed_location": {
                "name": biz_res.location.name,
                "district": biz_res.location.district,
                "state": biz_res.location.state,
                "country": biz_res.location.country,
                "latitude": biz_res.location.latitude,
                "longitude": biz_res.location.longitude,
                "source": biz_res.location.source
            },
            "entrepreneur_skills": biz_res.skills,
            "skills_status": biz_res.skills_status,
            "experience_years": biz_res.experience_years,
            "product_service": biz_res.product_service,
            "products": biz_res.products,
            "language": {
                "code": lang_info.code,
                "locale": lang_info.locale,
                "name": lang_info.name,
                "confidence": lang_info.confidence,
                "is_hinglish": lang_info.is_hinglish
            },
            "provenance": {
                "available_capital": asdict(amount_res.provenance) if amount_res.provenance else None,
                "extraction_method": "DETERMINISTIC_CANONICAL"
            },
            "confidence": {
                "business_concept": 0.95 if biz_res.business_concept else 0.0,
                "intent": 0.92 if biz_res.intent != "unknown" else 0.40,
                "available_capital": 0.98 if amount_res.available_capital is not None else 0.0,
                "proposed_location": 0.92 if (biz_res.location.district or biz_res.location.name) else 0.0,
                "entrepreneur_skills": 0.90 if biz_res.skills_status in ["collected", "no_experience"] else 0.0
            }
        }

        # 6. Optional LLM Refinement Attempt (Graceful Fallback on any failure)
        refined_profile = deterministic_profile
        if use_llm_refinement and settings.is_llm_configured:
            try:
                refined_profile = await self._attempt_llm_refinement(
                    text=clean_text,
                    lang_info=lang_info,
                    deterministic=deterministic_profile
                )
            except Exception as e:
                logger.warning(f"[INTAKE LLM REFINEMENT FALLBACK] Failed ({e}), using deterministic profile.")
                refined_profile = deterministic_profile

        # 7. Post-Validation and Provenance Enforcement
        validated_profile = self._validate_and_enforce_canonical_rules(refined_profile, deterministic_profile)
        return validated_profile

    async def _attempt_llm_refinement(
        self,
        text: str,
        lang_info: LanguageInfo,
        deterministic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attempts structured JSON completion from LLM with strict merging safeguards.
        """
        prompt = f"""You are a strict data extraction engine for the KALPA rural entrepreneurship advisory system.
Extract structured entities from the user's business description into strict JSON.

CRITICAL RULES:
1. Output ONLY valid JSON matching the exact schema below.
2. If money/capital was already detected by the deterministic normalizer ({deterministic.get('available_capital')}), PRESERVE IT.
3. If location is mentioned, extract name, district, and state accurately. User location ALWAYS takes priority.
4. If skills are mentioned, list them. If the user explicitly stated they have no experience, set skills_status="no_experience".

USER INPUT: "{text}"
LANGUAGE: {lang_info.name} ({lang_info.locale})

CURRENT DETERMINISTIC ENTITIES:
{json.dumps(deterministic, ensure_ascii=False)}

REQUIRED JSON OUTPUT FORMAT:
{{
  "business_concept": string or null,
  "business_category_hint": string or null,
  "intent": "start_business" | "expand_business" | "existing_business" | "unknown",
  "business_stage": "idea" | "planning" | "existing",
  "available_capital": integer in INR or null,
  "capital_currency": "INR",
  "proposed_location": {{
    "name": string,
    "district": string,
    "state": string,
    "country": "India",
    "latitude": null,
    "longitude": null,
    "source": "user" | "gps" | "unresolved"
  }},
  "entrepreneur_skills": [string],
  "skills_status": "collected" | "no_experience" | "unspecified"
}}"""

        messages = [
            {"role": "system", "content": "You are a JSON-only extraction system for Indian rural micro-enterprises."},
            {"role": "user", "content": prompt}
        ]

        result = await llm_client.chat_completion(
            messages=messages,
            json_mode=True,
            max_tokens=350,
            temperature=0.0,
            timeout=10.0
        )

        if not result or not isinstance(result, dict):
            logger.info("[INTAKE LLM REFINEMENT] LLM returned empty or non-dict, using deterministic entities.")
            return deterministic

        # Merge safeguards: Deterministic high-confidence values take precedence for money
        merged = dict(deterministic)

        if result.get("business_concept") and not merged.get("business_concept"):
            merged["business_concept"] = result["business_concept"]
            merged["business_category_hint"] = result.get("business_category_hint") or "General Micro Enterprise"

        # Deterministic capital ALWAYS overrides or preserves
        if deterministic.get("available_capital") is not None:
            merged["available_capital"] = deterministic["available_capital"]
            merged["capital_currency"] = "INR"
        elif result.get("available_capital") is not None and isinstance(result["available_capital"], (int, float)):
            merged["available_capital"] = int(result["available_capital"])
            merged["capital_currency"] = "INR"

        # Location merge
        det_loc = deterministic.get("proposed_location", {})
        res_loc = result.get("proposed_location", {})
        if isinstance(res_loc, dict):
            if not det_loc.get("district") and res_loc.get("district"):
                merged["proposed_location"]["district"] = res_loc["district"]
            if not det_loc.get("name") and res_loc.get("name"):
                merged["proposed_location"]["name"] = res_loc["name"]
            if not det_loc.get("state") and res_loc.get("state"):
                merged["proposed_location"]["state"] = res_loc["state"]
            if res_loc.get("district") or res_loc.get("name"):
                merged["proposed_location"]["source"] = "user"

        # Skills merge
        if result.get("entrepreneur_skills") and isinstance(result["entrepreneur_skills"], list):
            existing_skills = set(merged.get("entrepreneur_skills", []))
            for sk in result["entrepreneur_skills"]:
                if isinstance(sk, str) and sk.strip():
                    existing_skills.add(sk.strip())
            merged["entrepreneur_skills"] = list(existing_skills)
            if merged["entrepreneur_skills"] and merged.get("skills_status") == "unspecified":
                merged["skills_status"] = "collected"

        if result.get("skills_status") == "no_experience":
            merged["skills_status"] = "no_experience"
            merged["entrepreneur_skills"] = []

        merged["provenance"]["extraction_method"] = "HYBRID_LLM_DETERMINISTIC"
        return merged

    def _validate_and_enforce_canonical_rules(
        self,
        profile: Dict[str, Any],
        deterministic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates all fields:
        - available_capital MUST be an integer or None (reject strings or unparsed text)
        - currency MUST be INR
        - confidence scores must accurately reflect field presence
        """
        result = dict(profile)

        # Money validation
        cap = result.get("available_capital")
        if cap is not None:
            if isinstance(cap, (int, float)):
                result["available_capital"] = int(cap)
            elif isinstance(cap, str):
                # Try parsing if LLM or pipeline returned string
                try:
                    result["available_capital"] = int(cap)
                except ValueError:
                    result["available_capital"] = deterministic.get("available_capital")
        else:
            result["available_capital"] = deterministic.get("available_capital")

        result["capital_currency"] = "INR"

        # Confidence recalculation
        confidence = {
            "business_concept": 0.95 if result.get("business_concept") else 0.0,
            "intent": 0.92 if result.get("intent") and result["intent"] != "unknown" else 0.40,
            "available_capital": 0.98 if result.get("available_capital") is not None else 0.0,
            "proposed_location": 0.92 if (result.get("proposed_location", {}).get("district") or result.get("proposed_location", {}).get("name")) else 0.0,
            "entrepreneur_skills": 0.90 if result.get("skills_status") in ["collected", "no_experience"] else 0.0
        }
        result["confidence"] = confidence

        return result

    def _build_empty_profile(self, lang_info: LanguageInfo) -> Dict[str, Any]:
        return {
            "business_concept": None,
            "business_category_hint": None,
            "intent": "start_business",
            "business_stage": "planning",
            "available_capital": None,
            "capital_currency": "INR",
            "currency_source": "NONE",
            "loan_requested": None,
            "proposed_location": {
                "name": "",
                "district": "",
                "state": "",
                "country": "India",
                "latitude": None,
                "longitude": None,
                "source": "unresolved"
            },
            "entrepreneur_skills": [],
            "skills_status": "unspecified",
            "experience_years": None,
            "product_service": None,
            "products": [],
            "language": {
                "code": lang_info.code,
                "locale": lang_info.locale,
                "name": lang_info.name,
                "confidence": lang_info.confidence,
                "is_hinglish": lang_info.is_hinglish
            },
            "provenance": {
                "available_capital": None,
                "extraction_method": "EMPTY_INPUT"
            },
            "confidence": {
                "business_concept": 0.0,
                "intent": 0.0,
                "available_capital": 0.0,
                "proposed_location": 0.0,
                "entrepreneur_skills": 0.0
            }
        }


canonical_intake_extractor = CanonicalIntakeExtractor()
