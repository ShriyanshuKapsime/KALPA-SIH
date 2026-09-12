"""
Comprehensive Integration Tests for Sarvam LLM Parser, Saree Default Elimination,
Cache Isolation, Semantic Contamination Protection, and Fail-Closed Execution.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.sarvam_llm_service import (
    extract_llm_content,
    extract_json_from_text,
    SarvamLLMService,
    LLMCollectionPlanOutput,
    check_llm_plan_semantic_cleanliness,
    ALLOWED_STAGE5_TOOLS
)
from app.agents.market_intelligence.context_normalizer import BusinessContextNormalizer
from app.agents.market_intelligence.execution.caching import MarketEvidenceCache
from app.agents.market_intelligence.planner import MarketRequirementPlanner, DeterministicMarketRequirementPlanner
from app.agents.market_intelligence.market_agent import market_intelligence_agent
from app.schemas.market import (
    CanonicalBusinessContext,
    MarketExecutionContext,
    LocationContext,
    ExecutionMetadata,
    CollectionPlan,
)


# ============================================================================
# TEST 1: Sarvam HTTP 200 + string content → llm_used=True, fallback=False
# ============================================================================

def test_extract_llm_content_string():
    """Standard OpenAI response with content as plain JSON string."""
    response = {
        "id": "chatcmpl-abc123",
        "model": "sarvam-105b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": '{"requirements": ["milch_livestock_population", "cattle_feed_wholesale_access"], "selected_tools": ["demographics_tool", "supply_access_tool"], "reasoning": "Dairy data plan", "suggested_focus_areas": ["feed"]}'
            },
            "finish_reason": "stop"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is True
    assert result["content"] is not None
    assert result["response_type"] in ["STRING_JSON", "STRING_TEXT"]
    assert result["error"] is None

    parsed = json.loads(result["content"])
    assert "requirements" in parsed
    assert "selected_tools" in parsed
    assert "milch_livestock_population" in parsed["requirements"]


# ============================================================================
# TEST 2: Sarvam HTTP 200 + list/block content → llm_used=True, fallback=False
# ============================================================================

def test_extract_llm_content_array_blocks():
    """OpenAI-compatible response with content as list of text blocks."""
    response = {
        "id": "chatcmpl-xyz789",
        "model": "sarvam-105b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": '{"requirements": ["milk_demand"],'},
                    {"type": "text", "text": '"selected_tools": ["demand_evidence_tool"], "reasoning": "dairy", "suggested_focus_areas": []}'}
                ]
            },
            "finish_reason": "stop"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is True
    assert result["content"] is not None
    assert result["response_type"] == "CONTENT_BLOCKS"
    assert result["error"] is None

    parsed = json.loads(result["content"])
    assert parsed["requirements"] == ["milk_demand"]
    assert parsed["selected_tools"] == ["demand_evidence_tool"]


# ============================================================================
# TEST 3: Sarvam HTTP 200 + reasoning plus valid content → llm_used=True, fallback=False
# ============================================================================

def test_extract_llm_content_reasoning_and_content():
    """Model returns both reasoning_content and valid final content string."""
    response = {
        "id": "chatcmpl-reasoning-1",
        "model": "sarvam-105b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "reasoning_content": "The user wants a collection plan for dairy farming in Chatra. I will select demographics and supply access tools.",
                "content": '{"requirements": ["milch_livestock_population"], "selected_tools": ["demographics_tool", "supply_access_tool"], "reasoning": "Selected based on dairy needs", "suggested_focus_areas": ["livestock"]}'
            },
            "finish_reason": "stop"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is True
    assert result["content"] is not None
    # Content must be the actual final JSON, not raw reasoning thoughts
    parsed = json.loads(result["content"])
    assert parsed["requirements"] == ["milch_livestock_population"]
    assert parsed["reasoning"] == "Selected based on dairy needs"


def test_extract_llm_content_reasoning_with_embedded_json():
    """Model returns reasoning_content with embedded markdown JSON and empty content."""
    response = {
        "id": "chatcmpl-reasoning-2",
        "model": "sarvam-105b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "reasoning_content": 'Here is my thinking:\n```json\n{"requirements": ["paddy_acreage"], "selected_tools": ["dataset_retrieval_tool"], "reasoning": "rice mill plan", "suggested_focus_areas": []}\n```\nDone.'
            },
            "finish_reason": "stop"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is True
    assert result["response_type"] == "REASONING_EMBEDDED_JSON"
    parsed = json.loads(result["content"])
    assert parsed["requirements"] == ["paddy_acreage"]


# ============================================================================
# TEST 4: Sarvam HTTP 200 + malformed response → exact parse failure reason
# ============================================================================

def test_extract_llm_content_token_limit_exceeded():
    """Model exhausted max_tokens during reasoning phase without generating content."""
    response = {
        "id": "chatcmpl-truncated",
        "model": "sarvam-105b",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "reasoning_content": "The user wants a plan for dairy. Step 1: analyze geography. Step 2: assess livestock density..."
            },
            "finish_reason": "length"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is False
    assert result["content"] is None
    assert result["response_type"] == "TOKEN_LIMIT_EXCEEDED"
    assert "token limit exceeded" in result["error"].lower()


def test_extract_llm_content_empty_choices():
    response = {"choices": []}
    result = extract_llm_content(response)
    assert result["success"] is False
    assert result["response_type"] == "MISSING_CHOICES"
    assert "missing or empty" in result["error"]


def test_extract_llm_content_refusal():
    response = {
        "choices": [{
            "message": {"role": "assistant", "content": None, "refusal": "I cannot fulfill this request."},
            "finish_reason": "stop"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is False
    assert result["response_type"] == "MODEL_REFUSAL"
    assert "refused" in result["error"].lower()


# ============================================================================
# TEST 5: User asks for dairy business → business_id != saree_retail
# ============================================================================

def test_dairy_never_returns_saree():
    canonical = BusinessContextNormalizer.normalize({
        "business_profile": {
            "specific_business": "Commercial Dairy Farm (10-Cow Unit)",
            "sector": "Animal Husbandry"
        }
    })
    assert canonical.business_id == "dairy_farm"
    assert canonical.business_id != "saree_retail"
    assert "saree" not in canonical.business_id


# ============================================================================
# TEST 6: User asks for mobile repair → business_id != saree_retail
# ============================================================================

def test_mobile_repair_never_saree():
    canonical = BusinessContextNormalizer.normalize({
        "business_profile": {
            "specific_business": "Mobile Phone Repair Shop",
            "sector": "Electronics Service"
        }
    })
    assert canonical.business_id != "saree_retail"
    assert "saree" not in canonical.business_id.lower()
    assert "mobile" in canonical.business_id.lower()


# ============================================================================
# TEST 7: User asks for saree shop → business_id=saree_retail
# ============================================================================

def test_saree_correctly_returns_saree_retail():
    canonical = BusinessContextNormalizer.normalize({
        "business_profile": {
            "specific_business": "Saree & Traditional Apparel Retail",
            "sector": "Retail Trade"
        }
    })
    assert canonical.business_id == "saree_retail"


# ============================================================================
# TEST 8: Cache contains old saree result but current request is dairy farming
# → CACHE INVALIDATED, NO saree data returned
# ============================================================================

def test_cache_invalidates_on_business_mismatch_and_purges_contaminated_saree():
    cache = MarketEvidenceCache()
    cache.clear()

    dairy = BusinessContextNormalizer.normalize({"business_profile": {"specific_business": "Dairy Farm"}})
    saree = BusinessContextNormalizer.normalize({"business_profile": {"specific_business": "Saree Retail"}})

    ctx_saree = MarketExecutionContext(
        analysis_id="analysis_saree", session_id="sess_saree",
        business=saree,
        location=LocationContext(resolved_location={"district": "Chatra", "state": "Jharkhand"}),
        force_refresh=False
    )
    ctx_dairy = MarketExecutionContext(
        analysis_id="analysis_dairy", session_id="sess_dairy",
        business=dairy,
        location=LocationContext(resolved_location={"district": "Chatra", "state": "Jharkhand"}),
        force_refresh=False
    )

    # Store saree data
    cache.set("demographics_tool", ctx_saree, {"data": "saree_demographics_result", "business": "saree_retail"})

    # Invalidate contaminated saree cache when running dairy
    cache.invalidate_contaminated_saree_cache("dairy_farm")

    # Dairy request must NOT receive saree data
    dairy_hit = cache.get("demographics_tool", ctx_dairy)
    assert dairy_hit is None


# ============================================================================
# TEST 9: LLM parsing succeeds → Stage 5 collection plan uses LLM business context
# ============================================================================

@pytest.mark.asyncio
async def test_llm_parsing_success_uses_llm_plan_without_saree_fallback():
    planner = MarketRequirementPlanner()
    dairy = BusinessContextNormalizer.normalize({"business_profile": {"specific_business": "Commercial Dairy Farm"}})

    mock_llm_output = LLMCollectionPlanOutput(
        requirements=["milch_cattle_density", "veterinary_access_index"],
        selected_tools=["demographics_tool", "supply_access_tool", "location_intelligence_tool", "knowledge_hub_tool"],
        reasoning="Tailored LLM plan for commercial dairy in Chatra",
        suggested_focus_areas=["Livestock mapping"]
    )

    with patch.object(planner.llm_service, "plan_market_collection", new_callable=AsyncMock) as mock_plan:
        mock_plan.return_value = mock_llm_output
        planner.llm_service.last_telemetry = {
            "sarvam_request_success": True,
            "sarvam_http_status": 200,
            "sarvam_response_received": True,
            "sarvam_response_shape": "STRING_JSON",
            "sarvam_content_extracted": True,
            "sarvam_response_parsed": True,
            "sarvam_schema_valid": True,
            "sarvam_fallback_triggered": False,
            "sarvam_fallback_reason": None,
            "execution_state": "LLM_SUCCESS"
        }

        plan, llm_used, fallback_used = await planner.plan_collection(dairy, {}, force_llm=True)

        assert llm_used is True
        assert fallback_used is False
        assert plan.planner == "llm"
        assert plan.business_id == "dairy_farm"
        assert "milch_cattle_density" in plan.requirements
        assert "saree" not in " ".join(plan.requirements)


# ============================================================================
# TEST 10: Semantic Contamination Gate (Rejects saree hallucinations in dairy)
# ============================================================================

def test_semantic_contamination_gate():
    mismatched_output = LLMCollectionPlanOutput(
        requirements=["female_population_density", "saree_handloom_clusters", "wedding_seasonality"],
        selected_tools=["demographics_tool"],
        reasoning="We should check silk and saree stores for this dairy farm."
    )
    is_clean, reason = check_llm_plan_semantic_cleanliness("Commercial Dairy Farm", "dairy_farm", mismatched_output)
    assert is_clean is False
    assert "Semantic contamination" in reason
    assert any(term in reason.lower() for term in ["saree", "handloom", "silk", "ethnic wear"])


# ============================================================================
# TEST 11: Fail-Closed & Telemetry Accuracy
# ============================================================================

def test_execution_metadata_telemetry():
    meta = ExecutionMetadata(
        llm_used=True,
        llm_fallback_used=False,
        execution_state="LLM_SUCCESS",
        sarvam_request_success=True,
        sarvam_http_status=200,
        sarvam_response_received=True,
        sarvam_response_shape="STRING_JSON",
        sarvam_content_extracted=True,
        sarvam_response_parsed=True,
        sarvam_schema_valid=True,
        sarvam_fallback_triggered=False,
        sarvam_fallback_reason=None
    )
    assert meta.execution_state == "LLM_SUCCESS"
    assert meta.sarvam_schema_valid is True
    assert meta.sarvam_fallback_triggered is False


# ============================================================================
# TEST 12: Tool calls extraction
# ============================================================================

def test_extract_llm_content_tool_calls():
    response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "plan_collection",
                        "arguments": '{"requirements": ["veterinary_proximity"], "selected_tools": ["supply_access_tool"], "reasoning": "via function calling", "suggested_focus_areas": []}'
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }]
    }
    result = extract_llm_content(response)
    assert result["success"] is True
    assert result["response_type"] == "TOOL_CALLS"
    parsed = json.loads(result["content"])
    assert parsed["requirements"] == ["veterinary_proximity"]
