import json
from typing import Dict, Any, List, Optional
from app.services.llm_client import llm_client
from app.core.config import settings
from app.core.logging import logger


async def classify_with_llm(
    business_text: str,
    normalized_concept: str,
    language_code: str,
    ontology_candidates: List[Dict[str, Any]],
    nic_candidates: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Controlled Groq LLM classification assistant.
    Strictly restricted to reasoning and choosing the best candidate from the supplied list.
    The LLM cannot invent new categories or codes.
    Deterministic validation remains authoritative.
    """
    if not settings.is_llm_configured:
        logger.info("[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: API key not configured")
        return None

    if not ontology_candidates:
        logger.info("[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: No ontology candidates to rank")
        return None

    logger.info(
        f"[LLM CLASSIFIER REQUEST] input='{business_text[:80]}' "
        f"normalized='{normalized_concept}' "
        f"ontology_candidates={len(ontology_candidates)} "
        f"nic_candidates={len(nic_candidates)}"
    )

    ontology_options = [
        {
            "candidate_id": c.get("id"),
            "sector": c.get("sector"),
            "category": c.get("category"),
            "sub_category": c.get("sub_category"),
            "specific_business": c.get("specific_business")
        }
        for c in ontology_candidates
    ]

    nic_options = [
        {
            "code": c.get("code"),
            "title": c.get("title")
        }
        for c in nic_candidates
    ]

    prompt = f"""You are the strict classification judge for the KALPA rural entrepreneurship system.
Your job is to SELECT the single best matching business ontology node and matching NIC code for the user's venture.

CRITICAL CONSTRAINTS:
1. You MUST ONLY choose from the provided ONTOLOGY CANDIDATES and NIC CANDIDATES.
2. DO NOT invent new sectors, categories, or NIC codes.
3. If the input is genuinely ambiguous (e.g. "clothing business" without saying whether it is sarees, readymade garments, or tailoring), set is_ambiguous=true.

USER INPUT: "{business_text}"
NORMALIZED CONCEPT: "{normalized_concept}"
DETECTED LANGUAGE: {language_code}

ONTOLOGY CANDIDATES:
{json.dumps(ontology_options, ensure_ascii=False, indent=2)}

NIC CANDIDATES:
{json.dumps(nic_options, ensure_ascii=False, indent=2)}

RETURN STRICT JSON FORMAT:
{{
  "selected_ontology_id": string (must match one candidate_id from list) or null,
  "selected_nic_code": string (must match one code from list) or null,
  "confidence_score": float (0.0 to 1.0),
  "is_ambiguous": boolean,
  "reason": string
}}"""

    messages = [
        {"role": "system", "content": "You are a deterministic classification judge outputting JSON only."},
        {"role": "user", "content": prompt}
    ]

    try:
        result = await llm_client.chat_completion(
            messages=messages,
            json_mode=True,
            max_tokens=300,
            temperature=0.0,
            timeout=15.0
        )

        if not result or not isinstance(result, dict):
            logger.info("[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: Empty response")
            return None

        # Validate that selected_ontology_id is from the candidate list
        valid_ont_ids = {c.get("id") for c in ontology_candidates if c.get("id")}
        if result.get("selected_ontology_id") and result.get("selected_ontology_id") not in valid_ont_ids:
            logger.warning(
                f"[LLM CLASSIFIER] Hallucinated ontology ID '{result.get('selected_ontology_id')}' rejected. "
                f"Falling back to deterministic candidate."
            )
            result["selected_ontology_id"] = ontology_candidates[0].get("id")

        # Validate that selected_nic_code is from the candidate list
        valid_nic_codes = {c.get("code") for c in nic_candidates if c.get("code")}
        if result.get("selected_nic_code") and valid_nic_codes and result.get("selected_nic_code") not in valid_nic_codes:
            logger.warning(
                f"[LLM CLASSIFIER] Hallucinated NIC code '{result.get('selected_nic_code')}' rejected. "
                f"Falling back to deterministic candidate."
            )
            result["selected_nic_code"] = nic_candidates[0].get("code")

        logger.info(
            f"[LLM CLASSIFIER SUCCESS] Selected ID: {result.get('selected_ontology_id')}, "
            f"NIC: {result.get('selected_nic_code')}, "
            f"Conf: {result.get('confidence_score')}"
        )
        return result

    except Exception as e:
        logger.warning(f"[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: {e}")
        return None
