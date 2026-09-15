"""
Entity Extractor Service for KALPA Stage 1.
Provides deterministic entity extraction and LLM structured refinement,
delegating to the dedicated, testable canonical extraction engine in app.services.intake.
"""

from typing import Dict, Any, List, Optional
from app.services.intake.canonical_extractor import canonical_intake_extractor
from app.services.intake.business_entity_extractor import (
    extract_multilingual_business_entities,
    MULTILINGUAL_BUSINESS_PATTERNS as BUSINESS_PATTERNS,
    KNOWN_LOCATIONS
)
from app.services.intake.amount_parser import parse_canonical_amount
from app.services.intake.language_normalizer import normalize_indic_numerals as normalize_indic_digits


def extract_deterministic_entities(text: str, language_code: str = "en") -> Dict[str, Any]:
    """
    Performs deterministic rule-based, dictionary, and regex extraction across multilingual text.
    Handles English, Kannada, Hindi, Marathi, Tamil, Telugu, and Hinglish inputs natively.
    """
    if not text:
        text = ""

    amount_res = parse_canonical_amount(text, language_code=language_code)
    biz_res = extract_multilingual_business_entities(text, language_code=language_code)

    capital = amount_res.available_capital
    currency = amount_res.currency

    confidence = {
        "business_concept": 0.95 if biz_res.business_concept else 0.0,
        "intent": 0.90 if biz_res.intent != "unknown" else 0.40,
        "available_capital": 0.98 if capital is not None else 0.0,
        "proposed_location": 0.92 if (biz_res.location.district or biz_res.location.name) else 0.0,
        "entrepreneur_skills": 0.90 if biz_res.skills_status in ["collected", "no_experience"] else 0.0
    }

    return {
        "business_concept": biz_res.business_concept,
        "business_category_hint": biz_res.business_category_hint,
        "intent": biz_res.intent,
        "business_stage": biz_res.business_stage,
        "available_capital": capital,
        "capital_currency": currency,
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
        "existing_business": {
            "exists": biz_res.intent in ["expand_business", "existing_business"],
            "type": biz_res.business_concept or "",
            "current_status": "operational" if biz_res.intent in ["expand_business", "existing_business"] else ""
        },
        "product_service": biz_res.product_service,
        "products": biz_res.products,
        "confidence": confidence
    }


async def refine_with_llm(
    text: str,
    language_code: str,
    deterministic_entities: Dict[str, Any]
) -> Dict[str, Any]:
    """
    LLM extraction refiner.
    Enhances extraction for nuance while guaranteeing deterministic extraction integrity and offline stability.
    """
    profile = await canonical_intake_extractor.extract_canonical_profile(
        text=text,
        language_hint=language_code,
        use_llm_refinement=True
    )
    
    # Return structured dict compatible with existing callers
    return {
        "business_concept": profile.get("business_concept"),
        "business_category_hint": profile.get("business_category_hint"),
        "intent": profile.get("intent", "start_business"),
        "business_stage": profile.get("business_stage", "planning"),
        "available_capital": profile.get("available_capital"),
        "capital_currency": profile.get("capital_currency", "INR"),
        "proposed_location": profile.get("proposed_location", {}),
        "entrepreneur_skills": profile.get("entrepreneur_skills", []),
        "skills_status": profile.get("skills_status", "unspecified"),
        "existing_business": {
            "exists": profile.get("intent") in ["expand_business", "existing_business"],
            "type": profile.get("business_concept") or "",
            "current_status": "operational" if profile.get("intent") in ["expand_business", "existing_business"] else ""
        },
        "confidence": profile.get("confidence", {})
    }
