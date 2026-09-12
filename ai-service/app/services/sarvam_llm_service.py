"""
Sarvam LLM Service for KALPA Stage 5 Market Intelligence Agent.
Handles selective LLM reasoning for dynamic evidence requirement discovery
and tool selection using Sarvam AI (sarvam-105b) with strict JSON output validation,
robust multi-shape content extraction, sanitized telemetry, and semantic isolation.
"""
import re
import json
import httpx
from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.market import CanonicalBusinessContext


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extracts valid JSON string from raw text.
    Handles:
    - Pure JSON strings
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Embedded JSON surrounded by natural language commentary
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()

    # 1. Direct parse attempt
    if (cleaned.startswith("{") and cleaned.endswith("}")) or (cleaned.startswith("[") and cleaned.endswith("]")):
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            pass

    # 2. Markdown code block extraction ```json ... ``` or ``` ... ```
    fence_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, flags=re.IGNORECASE)
    for fm in fence_matches:
        fm_clean = fm.strip()
        try:
            json.loads(fm_clean)
            return fm_clean
        except Exception:
            pass

    # 3. Search for outermost JSON object {...}
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = cleaned[start_idx:end_idx + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    return None


def extract_llm_content(response_data: dict) -> Dict[str, Any]:
    """
    Robust content extractor for OpenAI-compatible LLM responses (Sarvam AI).
    Supports all response shapes:
    - content as string (clean JSON or text)
    - content as list / array of content blocks (OpenAI multimodal/vision format)
    - content blocks containing nested text objects
    - reasoning + content (extracts content, checks reasoning for embedded JSON if content missing)
    - tool call responses (tool_calls[0].function.arguments)
    - refusal responses
    - token limit truncation detection

    Returns a structured contract:
    SUCCESS:
    {
      "success": True,
      "content": "...",
      "response_type": "...",
      "error": None
    }
    OR FAILURE:
    {
      "success": False,
      "content": None,
      "response_type": "...",
      "error": "EXACT_REASON"
    }
    """
    if not isinstance(response_data, dict):
        return {
            "success": False,
            "content": None,
            "response_type": "INVALID_RESPONSE_FORMAT",
            "error": "Response data is not a JSON object."
        }

    choices = response_data.get("choices")
    if not choices or not isinstance(choices, list) or len(choices) == 0:
        return {
            "success": False,
            "content": None,
            "response_type": "MISSING_CHOICES",
            "error": "Response choices missing or empty."
        }

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return {
            "success": False,
            "content": None,
            "response_type": "INVALID_CHOICE_STRUCTURE",
            "error": "First choice element is not a dict."
        }

    finish_reason = first_choice.get("finish_reason", "unknown")
    msg = first_choice.get("message")
    if not msg or not isinstance(msg, dict):
        msg = first_choice.get("delta")
        if not msg or not isinstance(msg, dict):
            return {
                "success": False,
                "content": None,
                "response_type": "MISSING_MESSAGE",
                "error": "No message or delta structure found in choice."
            }

    # Case 1: Refusal check
    refusal = msg.get("refusal")
    if refusal and isinstance(refusal, str) and refusal.strip():
        logger.warning(f"[SARVAM LLM] Model refused request: {refusal[:200]}")
        return {
            "success": False,
            "content": None,
            "response_type": "MODEL_REFUSAL",
            "error": f"Model refused request: {refusal[:200]}"
        }

    # Case 2: Direct string content
    content = msg.get("content")
    if isinstance(content, str) and content.strip():
        extracted_json = extract_json_from_text(content)
        final_text = extracted_json if extracted_json is not None else content.strip()
        return {
            "success": True,
            "content": final_text,
            "response_type": "STRING_JSON" if extracted_json else "STRING_TEXT",
            "error": None
        }

    # Case 3: List / content blocks (multimodal / OpenAI block format)
    if isinstance(content, list) and len(content) > 0:
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    text_parts.append(block["text"])
                elif isinstance(block.get("text"), dict) and "value" in block["text"]:
                    text_parts.append(str(block["text"]["value"]))
                elif "content" in block and isinstance(block["content"], str):
                    text_parts.append(block["content"])
                elif "text" in block and isinstance(block["text"], str):
                    text_parts.append(block["text"])
        if text_parts:
            joined_text = "\n".join(text_parts).strip()
            extracted_json = extract_json_from_text(joined_text)
            final_text = extracted_json if extracted_json is not None else joined_text
            return {
                "success": True,
                "content": final_text,
                "response_type": "CONTENT_BLOCKS",
                "error": None
            }

    # Case 4: Tool call function arguments
    tool_calls = msg.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
        for tc in tool_calls:
            fn = (tc or {}).get("function", {})
            args = fn.get("arguments")
            if isinstance(args, str) and args.strip():
                extracted_json = extract_json_from_text(args) or args.strip()
                return {
                    "success": True,
                    "content": extracted_json,
                    "response_type": "TOOL_CALLS",
                    "error": None
                }
            elif isinstance(args, dict):
                return {
                    "success": True,
                    "content": json.dumps(args),
                    "response_type": "TOOL_CALLS_DICT",
                    "error": None
                }

    # Case 5: Reasoning / thinking field inspection
    for alt_field in ("reasoning_content", "reasoning", "thinking"):
        alt_val = msg.get(alt_field)
        if alt_val and isinstance(alt_val, str) and alt_val.strip():
            # Check if reasoning contains embedded valid JSON
            embedded_json = extract_json_from_text(alt_val)
            if embedded_json:
                logger.info(f"[SARVAM LLM] Extracted valid JSON structure from '{alt_field}'")
                return {
                    "success": True,
                    "content": embedded_json,
                    "response_type": "REASONING_EMBEDDED_JSON",
                    "error": None
                }
            
            # If token limit was exceeded during reasoning
            if finish_reason == "length":
                logger.warning(
                    f"[SARVAM LLM RESPONSE_PARSE_ERROR] Token limit exceeded during reasoning. "
                    f"reasoning_length={len(alt_val)}, finish_reason='{finish_reason}'"
                )
                return {
                    "success": False,
                    "content": None,
                    "response_type": "TOKEN_LIMIT_EXCEEDED",
                    "error": f"Max token limit exceeded during model reasoning phase before content was generated."
                }

            logger.warning(f"[SARVAM LLM RESPONSE_PARSE_ERROR] Model emitted reasoning thoughts without generating final content.")
            return {
                "success": False,
                "content": None,
                "response_type": "REASONING_WITHOUT_CONTENT",
                "error": "Model produced reasoning thoughts without emitting structured content."
            }

    # Case 6: Empty content with finish_reason logging
    raw_keys = list(msg.keys()) if isinstance(msg, dict) else []
    content_type = type(content).__name__
    logger.warning(
        f"[SARVAM LLM RESPONSE_PARSE_ERROR] Could not extract usable text. "
        f"content_type={content_type}, finish_reason='{finish_reason}', "
        f"message_keys={raw_keys}, model='{response_data.get('model', 'unknown')}'"
    )
    return {
        "success": False,
        "content": None,
        "response_type": "EMPTY_CONTENT",
        "error": f"Content string missing or empty from message (finish_reason={finish_reason})."
    }


def log_sanitized_sarvam_response(data: dict):
    """
    Safely logs a sanitized diagnostic view of the raw Sarvam LLM response.
    Never logs API keys or credentials.
    """
    choices = data.get("choices") or []
    first_choice = choices[0] if choices and isinstance(choices[0], dict) else {}
    msg = first_choice.get("message") or {}

    content_val = msg.get("content")
    reasoning_val = msg.get("reasoning_content") or msg.get("reasoning") or ""

    sanitized_summary = {
        "response_id": data.get("id", "unknown"),
        "model": data.get("model", "unknown"),
        "choices_count": len(choices),
        "finish_reason": first_choice.get("finish_reason", "unknown"),
        "message_keys": list(msg.keys()) if isinstance(msg, dict) else [],
        "content_type": type(content_val).__name__,
        "content_preview": str(content_val)[:150] if content_val is not None else None,
        "reasoning_length": len(str(reasoning_val)),
        "reasoning_preview": str(reasoning_val)[:150] if reasoning_val else None,
        "tool_calls_present": bool(msg.get("tool_calls")),
        "refusal": msg.get("refusal")
    }

    logger.info(f"[SARVAM RAW RESPONSE PIPELINE] {json.dumps(sanitized_summary)}")


# -----------------------------------------------------------------------------
# Semantic Contamination Gate
# -----------------------------------------------------------------------------

FORBIDDEN_DOMAIN_TERMS = {
    "dairy_farm": ["saree", "handloom", "banarasi", "silk saree", "ethnic wear", "bridal wear", "garment retail"],
    "rice_mill": ["saree", "handloom", "milch cow", "dairy farm", "silage"],
    "kirana_grocery": ["saree handloom", "banarasi silk", "paddy dehusking"],
    "two_wheeler_repair": ["saree", "handloom", "milch cattle", "paddy milling"],
    "welding_fabrication": ["saree", "handloom", "milch cattle"],
    "poultry_broiler": ["saree", "handloom", "silk retail"],
    "goat_farming": ["saree", "handloom", "silk retail"],
    "saree_retail": ["milch", "bovine", "cattle fodder", "chilling center", "paddy milling", "rubber roll"]
}


def check_llm_plan_semantic_cleanliness(
    concept: str,
    business_id: str,
    plan_output: "LLMCollectionPlanOutput"
) -> Tuple[bool, Optional[str]]:
    """
    Guarantees zero cross-business semantic contamination in LLM-generated plans.
    Rejects plans that hallucinate unrelated domain requirements (e.g. saree for dairy).
    """
    b_id_clean = business_id.lower().strip()
    concept_clean = concept.lower().strip()

    # Check against known domain forbidden keywords
    forbidden = FORBIDDEN_DOMAIN_TERMS.get(b_id_clean, [])
    if "saree" not in b_id_clean and "saree" not in concept_clean:
        forbidden = list(set(forbidden + ["saree", "banarasi silk", "ethnic wear"]))

    plan_corpus = " ".join(
        plan_output.requirements +
        [plan_output.reasoning] +
        plan_output.suggested_focus_areas
    ).lower()

    for term in forbidden:
        if term in plan_corpus:
            return False, f"Semantic contamination: forbidden domain term '{term}' generated for '{concept}' ({business_id})"

    return True, None


class LLMToolSelection(BaseModel):
    tool_name: str
    priority: str = "HIGH"  # HIGH | MEDIUM | LOW
    reason: str = ""


class LLMCollectionPlanOutput(BaseModel):
    requirements: List[str] = Field(default_factory=list)
    selected_tools: List[str] = Field(default_factory=list)
    reasoning: str = ""
    suggested_focus_areas: List[str] = Field(default_factory=list)


# Strict list of valid tools registered in Stage 5
ALLOWED_STAGE5_TOOLS = [
    "location_intelligence_tool",
    "demographics_tool",
    "competitor_discovery_tool",
    "demand_evidence_tool",
    "supply_access_tool",
    "infrastructure_access_tool",
    "economic_purchasing_power_tool",
    "dataset_retrieval_tool",
    "knowledge_hub_tool",
    "demand_prediction_adapter",
]


class SarvamLLMService:
    """
    Dedicated client for Sarvam AI LLM API (sarvam-105b).
    Enforces selective prompt execution, JSON schema adherence, safe fallback,
    and comprehensive execution telemetry.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = settings.SARVAM_LLM_MODEL or "sarvam-105b"
        self.endpoint = settings.SARVAM_LLM_ENDPOINT or "https://api.sarvam.ai/v1/chat/completions"
        self.last_telemetry: Dict[str, Any] = {}

    @property
    def is_available(self) -> bool:
        return settings.is_sarvam_llm_enabled

    async def health_check(self) -> Dict[str, Any]:
        """Performs a quick non-blocking health check on the Sarvam LLM provider."""
        if not self.is_available:
            return {
                "status": "unavailable",
                "configured": False,
                "model": self.model,
                "message": "Sarvam API key not configured or LLM disabled."
            }
        return {
            "status": "healthy",
            "configured": True,
            "model": self.model,
            "endpoint": self.endpoint
        }

    async def plan_market_collection(
        self,
        business_profile: Union[Dict[str, Any], CanonicalBusinessContext],
        knowledge_pack: Optional[Dict[str, Any]] = None,
        location_profile: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Optional[LLMCollectionPlanOutput]:
        """
        Invokes Sarvam LLM to reason over business type, location, and knowledge context
        to select relevant tools and outline data requirements.
        Enforces single-shot request, robust parsing, and semantic validation.
        Returns parsed LLMCollectionPlanOutput or None.
        """
        telemetry: Dict[str, Any] = {
            "sarvam_request_success": False,
            "sarvam_http_status": None,
            "sarvam_response_received": False,
            "sarvam_response_shape": None,
            "sarvam_content_extracted": False,
            "sarvam_response_parsed": False,
            "sarvam_schema_valid": False,
            "sarvam_response_validation_success": False,
            "sarvam_fallback_triggered": True,
            "sarvam_fallback_reason": None,
            "execution_state": "DETERMINISTIC_ONLY"
        }
        self.last_telemetry = telemetry

        if not self.is_available:
            telemetry["sarvam_fallback_reason"] = "LLM_NOT_CONFIGURED"
            telemetry["execution_state"] = "DETERMINISTIC_ONLY"
            logger.info("[SARVAM LLM] Sarvam LLM not configured/enabled. Triggering deterministic fallback.")
            return None

        if isinstance(business_profile, CanonicalBusinessContext):
            concept = business_profile.business_name or business_profile.specific_business or business_profile.business_id
            sector = business_profile.sector or "General"
            b_id = business_profile.business_id
        else:
            bus_sec = (business_profile or {}).get("business_profile") or {}
            concept = (
                bus_sec.get("specific_business") or
                bus_sec.get("business_name") or
                (business_profile or {}).get("specific_business") or
                "Rural Enterprise"
            )
            sector = bus_sec.get("sector") or (business_profile or {}).get("sector") or "General"
            b_id = bus_sec.get("business_id") or (business_profile or {}).get("business_id") or "enterprise"

        loc_sec = location_profile or (business_profile if isinstance(business_profile, dict) else {}).get("location_profile") or {}
        location_desc = f"{loc_sec.get('village') or ''}, {loc_sec.get('district') or ''}, {loc_sec.get('state') or 'India'}".strip(", ")

        demand_drivers = (knowledge_pack or {}).get("demand_drivers", [])
        catchment = (knowledge_pack or {}).get("catchment", {})

        system_prompt = (
            "You are the KALPA Market Intelligence Planning Agent for rural and semi-urban Indian enterprises.\n"
            "Think concisely and select relevant tools strictly from the registered list. Output pure JSON matching schema.\n\n"
            f"REGISTERED TOOLS (Choose ONLY from this exact list):\n"
            + "\n".join([f"- {t}" for t in ALLOWED_STAGE5_TOOLS])
            + "\n\nCRITICAL RULES:\n"
            "1. NEVER invent tool names outside the registered list.\n"
            "2. Return ONLY a valid JSON object matching schema without markdown code blocks or conversational text."
        )

        user_prompt = (
            f"Business: {concept} (ID: {b_id})\n"
            f"Sector: {sector}\n"
            f"Location: {location_desc}\n"
            f"Demand Drivers: {', '.join(demand_drivers) if demand_drivers else 'Standard catchment drivers'}\n"
            f"Catchment Radius: {catchment.get('primary_radius_km', 5.0)} km\n\n"
            "Output JSON Schema:\n"
            "{\n"
            '  "requirements": ["milch_livestock_density", "raw_material_supply_hubs", "competitor_density"],\n'
            '  "selected_tools": ["location_intelligence_tool", "demographics_tool", "supply_access_tool", "knowledge_hub_tool"],\n'
            '  "reasoning": "Direct explanation of why these tools and requirements are critical for this specific enterprise",\n'
            '  "suggested_focus_areas": ["Key area 1", "Key area 2"]\n'
            "}"
        )

        headers = {
            "api-subscription-key": self.api_key or "",
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
        }

        try:
            logger.info(f"[SARVAM LLM] Requesting collection plan from model='{self.model}' for '{concept}' (ID: {b_id})")
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(self.endpoint, headers=headers, json=payload)
                telemetry["sarvam_http_status"] = resp.status_code

                if resp.status_code != 200:
                    telemetry["sarvam_request_success"] = False
                    telemetry["sarvam_fallback_reason"] = f"HTTP_{resp.status_code}"
                    telemetry["execution_state"] = "LLM_FALLBACK"
                    logger.warning(
                        f"[SARVAM LLM FALLBACK] sarvam_request_success=False sarvam_http_status={resp.status_code} "
                        f"sarvam_fallback_triggered=True sarvam_fallback_reason=HTTP_{resp.status_code} | "
                        f"Response: {resp.text[:200]}"
                    )
                    return None

                telemetry["sarvam_request_success"] = True
                telemetry["sarvam_response_received"] = True

                data = resp.json()
                if not isinstance(data, dict):
                    telemetry["sarvam_fallback_reason"] = "RESPONSE_NOT_JSON_OBJECT"
                    telemetry["execution_state"] = "LLM_HTTP_SUCCESS_PARSE_FAILURE"
                    logger.warning("[SARVAM LLM ERROR] Response is not a JSON object.")
                    return None

                # Log sanitized raw response pipeline (Task 1)
                log_sanitized_sarvam_response(data)

                # -------------------------------------------------------
                # ROBUST CONTENT EXTRACTION (Task 2 & 3)
                # -------------------------------------------------------
                extract_res = extract_llm_content(data)
                telemetry["sarvam_response_shape"] = extract_res["response_type"]

                if not extract_res["success"] or not extract_res["content"]:
                    telemetry["sarvam_content_extracted"] = False
                    telemetry["sarvam_fallback_reason"] = extract_res["error"] or "CONTENT_EXTRACTION_FAILED"
                    telemetry["execution_state"] = "LLM_HTTP_SUCCESS_PARSE_FAILURE"
                    logger.warning(
                        f"[SARVAM LLM FALLBACK] sarvam_request_success=True sarvam_http_status=200 "
                        f"sarvam_response_received=True sarvam_response_shape={extract_res['response_type']} "
                        f"sarvam_content_extracted=False sarvam_fallback_triggered=True "
                        f"sarvam_fallback_reason={telemetry['sarvam_fallback_reason']}"
                    )
                    return None

                telemetry["sarvam_content_extracted"] = True
                content_text = extract_res["content"]

                # Parse JSON string
                try:
                    parsed = json.loads(content_text)
                except json.JSONDecodeError as jde:
                    telemetry["sarvam_response_parsed"] = False
                    telemetry["sarvam_fallback_reason"] = "JSON_DECODE_ERROR"
                    telemetry["execution_state"] = "LLM_HTTP_SUCCESS_PARSE_FAILURE"
                    logger.warning(
                        f"[SARVAM LLM FALLBACK] sarvam_request_success=True sarvam_http_status=200 "
                        f"sarvam_response_received=True sarvam_response_shape={extract_res['response_type']} "
                        f"sarvam_content_extracted=True sarvam_response_parsed=False "
                        f"sarvam_fallback_triggered=True sarvam_fallback_reason=JSON_DECODE_ERROR | {jde}"
                    )
                    return None

                if not isinstance(parsed, dict):
                    telemetry["sarvam_response_parsed"] = False
                    telemetry["sarvam_fallback_reason"] = "PARSED_JSON_NOT_DICT"
                    telemetry["execution_state"] = "LLM_HTTP_SUCCESS_PARSE_FAILURE"
                    logger.warning("[SARVAM LLM PARSE_ERROR] Parsed content is not a dict.")
                    return None

                telemetry["sarvam_response_parsed"] = True

                # Validate through Pydantic Schema
                try:
                    plan_output = LLMCollectionPlanOutput(**parsed)
                except ValidationError as ve:
                    telemetry["sarvam_schema_valid"] = False
                    telemetry["sarvam_response_validation_success"] = False
                    telemetry["sarvam_fallback_reason"] = "SCHEMA_VALIDATION_ERROR"
                    telemetry["execution_state"] = "LLM_SCHEMA_FAILURE"
                    logger.warning(
                        f"[SARVAM LLM FALLBACK] sarvam_request_success=True sarvam_http_status=200 "
                        f"sarvam_response_parsed=True sarvam_schema_valid=False "
                        f"sarvam_fallback_triggered=True sarvam_fallback_reason=SCHEMA_VALIDATION_ERROR | {ve}"
                    )
                    return None

                # Output Validation Gate: Semantic Contamination Check (Task 6)
                is_clean, contam_err = check_llm_plan_semantic_cleanliness(concept, b_id, plan_output)
                if not is_clean:
                    telemetry["sarvam_schema_valid"] = False
                    telemetry["sarvam_response_validation_success"] = False
                    telemetry["sarvam_fallback_reason"] = "BUSINESS_CONTEXT_MISMATCH"
                    telemetry["execution_state"] = "LLM_SCHEMA_FAILURE"
                    logger.warning(
                        f"[SARVAM LLM FALLBACK] sarvam_request_success=True sarvam_http_status=200 "
                        f"sarvam_response_parsed=True sarvam_schema_valid=False "
                        f"sarvam_fallback_triggered=True sarvam_fallback_reason=BUSINESS_CONTEXT_MISMATCH | {contam_err}"
                    )
                    return None

                telemetry["sarvam_schema_valid"] = True
                telemetry["sarvam_response_validation_success"] = True

                # Filter and enforce registered tools ONLY
                valid_tools = [t for t in plan_output.selected_tools if t in ALLOWED_STAGE5_TOOLS]

                # Ensure baseline essential tools are present
                if "location_intelligence_tool" not in valid_tools:
                    valid_tools.insert(0, "location_intelligence_tool")
                if "knowledge_hub_tool" not in valid_tools:
                    valid_tools.append("knowledge_hub_tool")
                if "demographics_tool" not in valid_tools:
                    valid_tools.append("demographics_tool")
                if "demand_evidence_tool" not in valid_tools:
                    valid_tools.append("demand_evidence_tool")

                plan_output.selected_tools = valid_tools
                telemetry["sarvam_fallback_triggered"] = False
                telemetry["sarvam_fallback_reason"] = None
                telemetry["execution_state"] = "LLM_SUCCESS"

                logger.info(
                    f"[SARVAM LLM SUCCESS] sarvam_request_success=True sarvam_http_status=200 "
                    f"sarvam_response_received=True sarvam_response_shape={extract_res['response_type']} "
                    f"sarvam_content_extracted=True sarvam_response_parsed=True "
                    f"sarvam_schema_valid=True sarvam_fallback_triggered=False "
                    f"execution_state=LLM_SUCCESS | "
                    f"Generated collection plan with {len(valid_tools)} tools for '{concept}'."
                )
                return plan_output

        except httpx.TimeoutException:
            telemetry["sarvam_request_success"] = False
            telemetry["sarvam_fallback_reason"] = "TIMEOUT"
            telemetry["execution_state"] = "LLM_FALLBACK"
            logger.warning(
                "[SARVAM LLM FALLBACK] sarvam_request_success=False sarvam_http_status=None "
                "sarvam_response_received=False sarvam_fallback_triggered=True "
                "sarvam_fallback_reason=TIMEOUT | Sarvam LLM request timed out."
            )
            return None
        except Exception as e:
            telemetry["sarvam_request_success"] = False
            telemetry["sarvam_fallback_reason"] = f"UNEXPECTED_ERROR_{type(e).__name__}"
            telemetry["execution_state"] = "LLM_FALLBACK"
            logger.warning(
                f"[SARVAM LLM FALLBACK] sarvam_request_success=False sarvam_fallback_triggered=True "
                f"sarvam_fallback_reason={telemetry['sarvam_fallback_reason']} | {e}"
            )
            return None


# Global singleton instance
sarvam_llm_service = SarvamLLMService()
