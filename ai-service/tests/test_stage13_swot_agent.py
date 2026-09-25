"""
Test Suite for Stage 13: Dynamic SWOT Agent.
Covers comprehensive verification scenarios:
- TEST 1: Balanced Positive SWOT for Strong Business
- TEST 2: Strong Market + Weak Entrepreneur Readiness -> Weakness Reflects Gap
- TEST 3: Poor Financial Viability / Tight DSCR -> Financial Weakness Appears
- TEST 4: High Seasonal Risk -> Seasonal Threat Appears
- TEST 5: Missing Stage Data -> Normalized and Handled without Hallucination
- TEST 6: Sarvam API Timeout -> Automatic Deterministic Fallback Triggered
- TEST 7: Sarvam Token Limit Exhaustion -> Automatic Deterministic Fallback Triggered
- TEST 8: Sarvam HTTP 500 Error -> Automatic Deterministic Fallback Triggered
- TEST 9: Sarvam Disabled / Unconfigured -> Automatic Deterministic Fallback Triggered
- TEST 10: Business Categories Contextualization
- TEST 11: Different User Profiles for Same Business -> Entrepreneur SWOT Changes
- TEST 12: Stage 12 = NOT_FEASIBLE -> Stage 13 YES-path Blocks Execution (BLOCKED_NOT_FEASIBLE)
- TEST 13: Stage 12 = VIABLE_WITH_CAUTION -> Stage 13 Executes with Conditions
"""
import pytest
import json
import httpx
from unittest.mock import patch, MagicMock

from app.schemas.swot import (
    SWOTEvaluationRequest,
    SWOTAnalysisResponse,
    SWOTItem,
    SWOTCategoryBreakdown,
    SWOTEvidenceRef,
    PriorityAction
)
from app.services.swot_engine.evidence_adapter import swot_evidence_adapter
from app.services.swot_engine.dynamic_swot_agent import DynamicSWOTAgent
from app.services.swot_engine.deterministic_fallback import generate_deterministic_swot_fallback
from app.services.swot_engine.prompt_builder import build_swot_system_prompt, build_swot_user_prompt


def create_mock_sarvam_response(
    strengths=None,
    weaknesses=None,
    opportunities=None,
    threats=None,
    position="Enterprise demonstrates sound operational fundamentals.",
    confidence=0.88
):
    return {
        "executive_summary": position,
        "strengths": strengths or [
            {
                "id": "ST-001",
                "title": "Demonstrated Domain Experience",
                "explanation": "Promoter has 3 years operating experience satisfying benchmark.",
                "evidence": ["Stage 10 Entrepreneur: experience score 100/100"],
                "source_stage": "STAGE_10"
            }
        ],
        "weaknesses": weaknesses or [
            {
                "id": "WK-001",
                "title": "Uncertified Formal Skill Training",
                "explanation": "Entrepreneur has not completed certified formal management training.",
                "evidence": ["Stage 10 Training: 0/100 uncertified"],
                "source_stage": "STAGE_10"
            }
        ],
        "opportunities": opportunities or [
            {
                "id": "OP-001",
                "title": "Strong Local Catchment Demand",
                "explanation": "High spatial demand density in local cluster.",
                "evidence": ["Stage 8 Opportunity: market opportunity score 88/100"],
                "source_stage": "STAGE_8"
            }
        ],
        "threats": threats or [
            {
                "id": "TH-001",
                "title": "Local Competitor Price Undercutting",
                "explanation": "Established nearby competitors may compete aggressively on margins.",
                "evidence": ["Stage 11 Risk: competition risk 0.35"],
                "source_stage": "STAGE_11"
            }
        ],
        "priority_actions": [
            {
                "action": "Complete RSETI or PMKVY micro-enterprise certification.",
                "reason": "Satisfies formal bank scheme criteria.",
                "priority": "HIGH",
                "source_stage": "STAGE_10"
            }
        ],
        "strategic_direction": position,
        "confidence": confidence
    }


# ==============================================================================
# TEST 1: Balanced Positive SWOT for Strong Business
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test1_balanced_positive():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-001",
        session_id="test-session-001",
        business_profile={"specific_business": "Saree Retail Store", "category": "Retail", "sector": "Apparel"},
        location_profile={"district": "Varanasi", "state": "Uttar Pradesh"},
        opportunity_result={"market_opportunity_score": 88.0, "demand_strength": "HIGH", "competitor_density": "LOW"},
        financial_analysis={"dscr": 1.85, "break_even_point_percentage": 45.0, "total_project_cost": 500000.0, "bank_loan_requirement": 350000.0},
        entrepreneur_readiness={"readiness_score": 90.0, "component_scores": {"experience": {"score": 100.0}, "skills": {"score": 90.0}, "training": {"score": 75.0}}},
        risk_analysis={"composite_risk_score": 0.22, "category_risks": {"FINANCIAL": {"score": 0.20}, "SEASONAL": {"score": 0.25}}},
        feasibility_result={"overall_feasibility_score": 85.0, "decision": "VIABLE", "recommendation": "YES"}
    )

    mock_llm_json = create_mock_sarvam_response(confidence=0.91)

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {"content": json.dumps(mock_llm_json)},
                "finish_reason": "stop"
            }]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.confidence == 0.91
        assert res.generation.mode == "SARVAM_LLM"
        assert res.generation.llm_status == "success"
        assert len(res.swot.strengths) >= 1
        assert res.swot.strengths[0].source_stage == "STAGE_10"
        assert res.strategic_summary.key_advantage != ""
        assert len(res.immediate_actions) >= 1


# ==============================================================================
# TEST 2: Strong Market + Weak Entrepreneur Readiness -> Weakness Reflects Gap
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test2_weak_readiness_gap():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-002",
        business_profile={"specific_business": "Kirana Store"},
        opportunity_result={"market_opportunity_score": 90.0},
        financial_analysis={"dscr": 1.55},
        entrepreneur_readiness={"readiness_score": 38.0, "component_scores": {"experience": {"score": 20.0}, "training": {"score": 0.0}}},
        risk_analysis={"composite_risk_score": 0.40},
        feasibility_result={"overall_feasibility_score": 62.0, "decision": "VIABLE_WITH_CAUTION", "recommendation": "CONDITIONAL"}
    )

    weaknesses = [
        {
            "id": "WK-001",
            "title": "Low Operating Experience and Training Gap",
            "explanation": "Entrepreneur lacks prior retail management experience and formal certification.",
            "evidence": ["Stage 10 Entrepreneur: readiness score 38/100"],
            "source_stage": "STAGE_10"
        }
    ]
    mock_llm_json = create_mock_sarvam_response(weaknesses=weaknesses)

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {"content": json.dumps(mock_llm_json)},
                "finish_reason": "stop"
            }]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert len(res.swot.weaknesses) >= 1
        assert res.swot.weaknesses[0].source_stage == "STAGE_10"


# ==============================================================================
# TEST 3: Poor Financial Viability / Tight DSCR -> Financial Weakness Appears
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test3_financial_weakness_threat():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-003",
        financial_analysis={"dscr": 1.15, "break_even_point_percentage": 78.0},
        risk_analysis={"category_risks": {"FINANCIAL": {"score": 0.72, "level": "HIGH"}}},
        feasibility_result={"overall_feasibility_score": 58.0, "decision": "VIABLE_WITH_CAUTION", "recommendation": "CONDITIONAL"}
    )

    weaknesses = [
        {
            "id": "WK-001",
            "title": "Tight Debt Servicing Cushion",
            "explanation": "Projected DSCR of 1.15x provides thin margin over monthly loan repayments.",
            "evidence": ["Stage 9 Finance: DSCR 1.15x", "Stage 11 Risk: financial risk HIGH (0.72)"],
            "source_stage": "STAGE_9"
        }
    ]
    mock_llm_json = create_mock_sarvam_response(weaknesses=weaknesses)

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.swot.weaknesses[0].source_stage == "STAGE_9"
        assert "1.15" in res.swot.weaknesses[0].explanation


# ==============================================================================
# TEST 4: High Seasonal Risk -> Seasonal Threat Appears
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test4_seasonal_threat():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-004",
        risk_analysis={"category_risks": {"SEASONAL": {"score": 0.78, "level": "HIGH"}}},
        feasibility_result={"overall_feasibility_score": 65.0, "decision": "VIABLE_WITH_CAUTION", "recommendation": "CONDITIONAL"}
    )

    threats = [
        {
            "id": "TH-001",
            "title": "Severe Seasonal Revenue Volatility",
            "explanation": "High revenue concentration during festive season creates lean cash flow in off-peak quarters.",
            "evidence": ["Stage 11 Risk: seasonal risk HIGH (0.78)"],
            "source_stage": "STAGE_11"
        }
    ]
    mock_llm_json = create_mock_sarvam_response(threats=threats)

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.swot.threats[0].source_stage == "STAGE_11"
        assert "Seasonal" in res.swot.threats[0].title or "seasonal" in res.swot.threats[0].explanation.lower()


# ==============================================================================
# TEST 5: Missing Stage Data -> Handled Gracefully
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test5_missing_market_data_gap():
    ctx = swot_evidence_adapter.extract_evidence_context(
        business_profile={"specific_business": "Rural Workshop"},
        opportunity_result=None,
        feasibility_result={"overall_feasibility_score": 60.0, "decision": "VIABLE_WITH_CAUTION"}
    )
    assert ctx["market"]["score"] == "Evidence unavailable"
    assert ctx["market"]["demand"] == "Evidence unavailable"


# ==============================================================================
# TEST 6: Sarvam API Timeout -> Automatic Deterministic Fallback Triggered
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test6_sarvam_timeout_deterministic_fallback():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-006",
        business_profile={"specific_business": "Saree Retail Store"},
        opportunity_result={"market_opportunity_score": 82.0},
        financial_analysis={"dscr": 1.65, "total_project_cost": 800000.0},
        entrepreneur_readiness={"readiness_score": 75.0, "component_scores": {"experience": {"score": 85.0}}},
        risk_analysis={"composite_risk_score": 0.28, "category_risks": {"COMPETITION": {"score": 0.45}}},
        feasibility_result={"overall_feasibility_score": 78.0, "decision": "VIABLE", "recommendation": "YES"}
    )

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):

        res = await agent.generate_swot_analysis(req)

        # Must trigger deterministic fallback, returning status COMPLETED without broken state
        assert res.status == "COMPLETED"
        assert res.generation.mode == "DETERMINISTIC_FALLBACK"
        assert res.generation.llm_status == "timeout"
        assert res.swot is not None
        assert len(res.swot.strengths) >= 1
        assert len(res.swot.priority_actions) >= 1
        assert "STAGE_10" in [s.source_stage for s in res.swot.strengths]


# ==============================================================================
# TEST 7: Sarvam Token Limit Exhaustion -> Automatic Deterministic Fallback
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test7_token_limit_exhaustion_fallback():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-007",
        business_profile={"specific_business": "Handloom Weaving"},
        financial_analysis={"dscr": 1.70},
        feasibility_result={"overall_feasibility_score": 80.0, "decision": "VIABLE"}
    )

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Simulating Sarvam token limit exhaustion during reasoning
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "reasoning_content": "Long chain of reasoning that consumed entire token budget..." * 50
                },
                "finish_reason": "length"
            }]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.generation.mode == "DETERMINISTIC_FALLBACK"
        assert res.generation.llm_status == "token_limit_exceeded"
        assert res.swot is not None
        assert len(res.swot.strengths) >= 1


# ==============================================================================
# TEST 8: Sarvam HTTP 500 Error -> Automatic Deterministic Fallback
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test8_http_500_fallback():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-008",
        business_profile={"specific_business": "Dairy Unit"},
        financial_analysis={"dscr": 1.50},
        feasibility_result={"overall_feasibility_score": 75.0, "decision": "VIABLE"}
    )

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.generation.mode == "DETERMINISTIC_FALLBACK"
        assert "http_500" in res.generation.llm_status
        assert res.swot is not None


# ==============================================================================
# TEST 9: Sarvam Disabled / Unconfigured -> Automatic Deterministic Fallback
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test9_sarvam_disabled_fallback():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-009",
        business_profile={"specific_business": "Apparel Boutique"},
        financial_analysis={"dscr": 1.60},
        feasibility_result={"overall_feasibility_score": 77.0, "decision": "VIABLE"}
    )

    with patch.object(DynamicSWOTAgent, "is_available", False):
        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.generation.mode == "DETERMINISTIC_FALLBACK"
        assert res.generation.llm_status == "unavailable"
        assert res.swot is not None


# ==============================================================================
# TEST 10: Business Categories Contextualization
# ==============================================================================
def test_swot_test10_business_category_context():
    ctx_dairy = swot_evidence_adapter.extract_evidence_context(
        business_profile={"specific_business": "Dairy Chilling Unit", "category": "Dairy / Agro-Processing"},
        location_profile={"district": "Anand", "state": "Gujarat"}
    )
    assert ctx_dairy["business"]["name"] == "Dairy Chilling Unit"
    assert ctx_dairy["business"]["domain"] == "Dairy / Agro-Processing"

    ctx_saree = swot_evidence_adapter.extract_evidence_context(
        business_profile={"specific_business": "Saree Retail Showroom", "category": "Retail"},
        location_profile={"district": "Surat", "state": "Gujarat"}
    )
    assert ctx_saree["business"]["name"] == "Saree Retail Showroom"
    assert ctx_saree["business"]["domain"] == "Retail"


# ==============================================================================
# TEST 11: Different User Profiles for Same Business
# ==============================================================================
def test_swot_test11_different_profiles_same_business():
    # Profile A: Veteran
    ctx_a = swot_evidence_adapter.extract_evidence_context(
        business_profile={"specific_business": "Saree Retail"},
        opportunity_result={"market_opportunity_score": 85.0},
        entrepreneur_readiness={"readiness_score": 92.0, "component_scores": {"experience": {"score": 100.0}}}
    )

    # Profile B: Novice
    ctx_b = swot_evidence_adapter.extract_evidence_context(
        business_profile={"specific_business": "Saree Retail"},
        opportunity_result={"market_opportunity_score": 85.0},
        entrepreneur_readiness={"readiness_score": 35.0, "component_scores": {"experience": {"score": 0.0}}}
    )

    assert ctx_a["market"]["score"] == ctx_b["market"]["score"] == 85.0
    assert ctx_a["entrepreneur"]["score"] == 92.0
    assert ctx_b["entrepreneur"]["score"] == 35.0


# ==============================================================================
# TEST 12: Stage 12 = NOT_FEASIBLE -> Blocks YES-path Execution
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test12_not_feasible_blocked():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-012",
        business_profile={"specific_business": "High Risk Speculative Venture"},
        feasibility_result={
            "overall_feasibility_score": 32.0,
            "decision": "NOT_FEASIBLE",
            "recommendation": "NO"
        }
    )

    res = await agent.generate_swot_analysis(req)

    assert res.status == "BLOCKED_NOT_FEASIBLE"
    assert res.swot is None
    assert "NOT_FEASIBLE" in res.message


# ==============================================================================
# TEST 13: Stage 12 = VIABLE_WITH_CAUTION -> Stage 13 Executes
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test13_viable_with_caution_executes():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-013",
        business_profile={"specific_business": "Poultry Farming"},
        feasibility_result={
            "overall_feasibility_score": 64.0,
            "decision": "VIABLE_WITH_CAUTION",
            "recommendation": "CONDITIONAL",
            "conditions": ["Maintain 2 months feed inventory buffer"]
        }
    )

    mock_llm_json = create_mock_sarvam_response(position="Venture is conditionally viable subject to operational safeguards.")

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post") as mock_post:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
        }
        mock_post.return_value = mock_resp

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.swot is not None
        assert "conditionally viable" in res.strategic_summary.business_position.lower()


# ==============================================================================
# TEST 14: Attempt 1 Timeout -> Attempt 2 Retry Succeeds with Compact Prompt
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test14_attempt1_timeout_attempt2_retry_success():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-014",
        business_profile={"specific_business": "Handloom Weaving"},
        feasibility_result={"overall_feasibility_score": 82.0, "decision": "VIABLE"}
    )

    mock_llm_json = create_mock_sarvam_response(position="Recovered on attempt 2.")

    mock_resp_success = MagicMock()
    mock_resp_success.status_code = 200
    mock_resp_success.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_llm_json)}}]
    }

    # First call times out, second call succeeds
    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post", side_effect=[httpx.TimeoutException("Read timed out"), mock_resp_success]):

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.generation.mode == "SARVAM_LLM"
        assert res.generation.llm_status == "success"
        assert res.swot is not None


# ==============================================================================
# TEST 15: Full Structured Schema Fields Validation (Impact, Mitigation, Roadmap)
# ==============================================================================
@pytest.mark.asyncio
async def test_swot_test15_full_schema_fields_grounded_validation():
    agent = DynamicSWOTAgent()

    req = SWOTEvaluationRequest(
        analysis_id="test-analysis-015",
        business_profile={"specific_business": "Organic Dairy"},
        feasibility_result={"overall_feasibility_score": 88.0, "decision": "VIABLE"}
    )

    custom_llm_json = {
        "executive_summary": "High growth potential organic dairy unit.",
        "strengths": [
            {
                "id": "ST-001",
                "title": "Chilling Infrastructure Access",
                "evidence": "Stage 6/8 infrastructure verified",
                "business_impact": "Prevents milk spoilage during evening collection",
                "priority": "HIGH",
                "source_stage": "STAGE_6",
                "data_status": "KNOWN"
            }
        ],
        "weaknesses": [
            {
                "id": "WS-001",
                "title": "Uncertified FSSAI Quality Audit",
                "evidence": "Stage 10 certification pending",
                "business_impact": "Delays institutional milk union supply contract",
                "priority": "HIGH",
                "source_stage": "STAGE_10",
                "data_status": "KNOWN"
            }
        ],
        "opportunities": [
            {
                "id": "OP-001",
                "title": "Value-Added Ghee and Paneer Processing",
                "evidence": "Stage 8 demand index 0.85",
                "action": "Procure small-scale cream separator",
                "priority": "HIGH",
                "source_stage": "STAGE_8",
                "data_status": "KNOWN"
            }
        ],
        "threats": [
            {
                "id": "TH-001",
                "title": "Summer Fodder Price Spike",
                "evidence": "Stage 11 seasonal risk 0.40",
                "business_impact": "Increases daily feed expense by 25%",
                "mitigation": "Establish silage storage silo in advance",
                "priority": "HIGH",
                "source_stage": "STAGE_11",
                "data_status": "KNOWN"
            }
        ],
        "strategic_priorities": [
            {
                "id": "SP-001",
                "action": "Procure silage pit and lock supply contract",
                "reason": "Protects feed margin during dry season",
                "linked_dimension": "finance",
                "priority": "HIGH"
            }
        ],
        "roadmap": [
            {"phase": "0-30 days", "actions": ["Obtain FSSAI license", "Construct silage pit"]},
            {"phase": "30-90 days", "actions": ["Procure milch cattle", "Connect with dairy cooperative"]},
            {"phase": "90+ days", "actions": ["Launch value-added paneer line"]}
        ],
        "strategic_direction": "Focus on value addition and fodder risk mitigation.",
        "confidence": 0.92
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(custom_llm_json)}}]
    }

    with patch.object(DynamicSWOTAgent, "is_available", True), \
         patch.object(agent, "is_available", True), \
         patch("httpx.AsyncClient.post", return_value=mock_resp):

        res = await agent.generate_swot_analysis(req)

        assert res.status == "COMPLETED"
        assert res.generation.mode == "SARVAM_LLM"
        assert len(res.swot.strengths) == 1
        assert res.swot.strengths[0].business_impact == "Prevents milk spoilage during evening collection"
        assert res.swot.threats[0].mitigation == "Establish silage storage silo in advance"
        assert res.swot.opportunities[0].action == "Procure small-scale cream separator"
        assert len(res.swot.roadmap) == 3
        assert res.swot.roadmap[0].phase == "0-30 days"
        assert "FSSAI" in res.swot.roadmap[0].actions[0]


# ==============================================================================
# TEST 16: Verify Bounded Interactive Timeout Configuration (<= 30s Budget)
# ==============================================================================
def test_swot_test16_timeout_configuration():
    agent = DynamicSWOTAgent()
    assert isinstance(agent.timeout, httpx.Timeout)
    assert agent.timeout.read == 14.0
    assert agent.timeout.connect == 5.0
    assert agent.timeout.write == 10.0
    assert agent.timeout.pool == 5.0

