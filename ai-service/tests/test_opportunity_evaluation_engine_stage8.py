"""
Comprehensive Test Suite for Stage 8: Opportunity Evaluation Engine.
Tests deterministic synthesis, Stage 7 ML graceful fallback, critical constraints,
level overrides, Saree Retail benchmark validation, orchestrator integration, and FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.opportunity_evaluation_engine import (
    OpportunityEvaluationEngine,
    opportunity_evaluation_engine,
    OPPORTUNITY_WEIGHTS,
    SUPPLY_WEIGHTS,
    OPPORTUNITY_LEVEL_THRESHOLDS,
    OpportunityLevel,
    DemandSourceType
)
from app.agents.adapters.opportunity_evaluation_adapter import OpportunityEvaluationAdapter
from app.agents.registry import agent_registry


@pytest.fixture
def saree_retail_stage6_payload():
    """
    Stage 6 output for Saree & Ethnic Wear Retail in Surat, Gujarat.
    Matches exact canonical values from specification.
    """
    return {
        "analysis_id": "saree-test-analysis-101",
        "session_id": "saree-test-session-101",
        "workflow": {
            "stage": 6,
            "state": "MARKET_INTELLIGENCE_ANALYZED",
            "status": "complete"
        },
        "business_context": {
            "business_id": "saree_retail",
            "specific_business": "Saree & Ethnic Wear Retail",
            "sector": "Retail Trade",
            "nic_code": "47711",
            "nic_name": "Retail sale of clothing, footwear and leather articles"
        },
        "location_context": {
            "district": "Surat",
            "state": "Gujarat",
            "country": "India"
        },
        "market_indicators": {
            "demand_evidence": {
                "demand_signal_strength": "STRONG",
                "demand_signal_score": 1.0,
                "data_coverage": 1.0,
                "confidence": 0.85
            },
            "competition": {
                "competitive_pressure_score": 0.18,
                "competitive_pressure": "LOW",
                "confidence": 0.86,
                "direct": {"count": 3}
            },
            "infrastructure": {
                "readiness": "AVAILABLE",
                "readiness_score": 1.0,
                "critical_gaps": [],
                "confidence": 0.90
            },
            "supply_ecosystem": {
                "supply_risk_score": 0.45,
                "critical_input_coverage": {"coverage_ratio": 1.0},
                "accessibility": "HIGH",
                "confidence": 0.82
            },
            "market_access": {
                "geographic_accessibility_score": 0.72,
                "accessibility": "HIGH",
                "confidence": 0.82
            },
            "market_capacity": {
                "status": "AVAILABLE",
                "net_capacity_score": 0.825,
                "capacity_signal": "EXPANSION_CAPACITY",
                "confidence": 0.85
            },
            "seasonality": {
                "annual_volatility": 0.35,
                "seasonal_risk": "MODERATE"
            }
        },
        "evidence_quality": {
            "overall_confidence": 0.84,
            "proxy_dependency": 0.53,
            "data_gaps": []
        }
    }


# -----------------------------------------------------------------------------
# Test 1: Saree Retail Exact Benchmark Validation
# -----------------------------------------------------------------------------
def test_saree_retail_benchmark_validation(saree_retail_stage6_payload):
    """
    Validates exact math for the Saree Retail benchmark:
    - Demand: 1.0 (weight 0.25) -> 0.25
    - Comp Opp: 1 - 0.18 = 0.82 (weight 0.20) -> 0.164
    - Infra: 1.0 (weight 0.15) -> 0.15
    - Supply: 0.60 * (1 - 0.45) + 0.40 * 1.0 = 0.73 (weight 0.15) -> 0.1095
    - Market Access: 0.72 (weight 0.10) -> 0.072
    - Market Capacity: 0.825 (weight 0.15) -> 0.12375
    - Base Sum = 0.86925 -> HIGH_OPPORTUNITY
    """
    res = opportunity_evaluation_engine.evaluate(saree_retail_stage6_payload)
    opp = res.opportunity_result

    assert opp.component_scores.demand.score == 1.0
    assert opp.component_scores.competition_opportunity.score == pytest.approx(0.82, rel=1e-3)
    assert opp.component_scores.infrastructure.score == 1.0
    assert opp.component_scores.supply_ecosystem.score == pytest.approx(0.73, rel=1e-3)
    assert opp.component_scores.market_access.score == pytest.approx(0.72, rel=1e-3)
    assert opp.component_scores.market_capacity.score == pytest.approx(0.825, rel=1e-3)

    assert opp.market_opportunity_score == pytest.approx(0.8693, abs=0.005)
    assert opp.level == OpportunityLevel.HIGH_OPPORTUNITY
    assert opp.demand_source.type == DemandSourceType.STAGE_6_DETERMINISTIC_EVIDENCE
    assert opp.demand_source.fallback_used is True
    assert opp.confidence > 0.70


# -----------------------------------------------------------------------------
# Test 2: High Demand + Saturated Market (Constraint Override)
# -----------------------------------------------------------------------------
def test_market_saturation_constraint_override(saree_retail_stage6_payload):
    """
    High demand (1.0) with SATURATED market capacity (0.20) must trigger constraint
    and cap opportunity level to LIMITED_OPPORTUNITY.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["market_capacity"] = {
        "status": "SATURATED",
        "net_capacity_score": 0.20,
        "capacity_signal": "HIGH_SATURATION",
        "confidence": 0.85
    }

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    # High demand should not allow HIGH_OPPORTUNITY
    assert opp.level in [OpportunityLevel.LIMITED_OPPORTUNITY, OpportunityLevel.LOW_OPPORTUNITY]
    assert opp.level_override is True
    assert any(c.constraint_id == "MARKET_SATURATION" for c in opp.constraints)


# -----------------------------------------------------------------------------
# Test 3: Missing Stage 7 ML -> Graceful Stage 6 Deterministic Demand Fallback
# -----------------------------------------------------------------------------
def test_missing_stage7_fallback_to_stage6(saree_retail_stage6_payload):
    """
    When Stage 7 ML is absent, Stage 8 must gracefully use Stage 6 demand evidence
    without failing or generating errors.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["demand_prediction"] = None

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert opp.demand_source.type == DemandSourceType.STAGE_6_DETERMINISTIC_EVIDENCE
    assert opp.demand_source.stage_7_available is False
    assert opp.demand_source.fallback_used is True
    assert res.execution_metadata.stage_7_ml_used is False


# -----------------------------------------------------------------------------
# Test 4: Stage 7 ML Prediction Available
# -----------------------------------------------------------------------------
def test_stage7_ml_prediction_ingestion(saree_retail_stage6_payload):
    """
    When Stage 7 ML prediction is provided, Stage 8 uses STAGE_7_ML demand source.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["demand_prediction"] = {
        "demand_index": 0.78,
        "level": "HIGH",
        "confidence": 0.71
    }

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert opp.demand_source.type == DemandSourceType.STAGE_7_ML
    assert opp.demand_source.stage_7_available is True
    assert opp.demand_source.fallback_used is False
    assert opp.component_scores.demand.score == pytest.approx(0.78, abs=0.01)
    assert res.execution_metadata.stage_7_ml_used is True


# -----------------------------------------------------------------------------
# Test 5: Infrastructure Critical Gap Constraint
# -----------------------------------------------------------------------------
def test_infrastructure_critical_gap_constraint(saree_retail_stage6_payload):
    """
    2+ critical infrastructure gaps should penalize infra score and cap opportunity level.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["infrastructure"] = {
        "readiness": "UNAVAILABLE",
        "readiness_score": 0.30,
        "critical_gaps": [
            {"requirement": "High Power 3-Phase Commercial Line", "status": "UNAVAILABLE"},
            {"requirement": "Adequate Water Discharge System", "status": "UNAVAILABLE"}
        ],
        "confidence": 0.75
    }

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert opp.component_scores.infrastructure.critical_gaps_count == 2
    assert opp.component_scores.infrastructure.gap_penalty > 0
    assert any(c.constraint_id == "CRITICAL_INFRASTRUCTURE_FAILURE" for c in opp.constraints)


# -----------------------------------------------------------------------------
# Test 6: Severe Supply Risk Penalty
# -----------------------------------------------------------------------------
def test_severe_supply_risk_penalty(saree_retail_stage6_payload):
    """
    Supply risk > 0.70 with input coverage < 0.40 triggers EXTREME_SUPPLY_FAILURE constraint.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["supply_ecosystem"] = {
        "supply_risk_score": 0.85,
        "critical_input_coverage": {"coverage_ratio": 0.25},
        "accessibility": "LOW",
        "confidence": 0.75
    }

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert any(c.constraint_id == "EXTREME_SUPPLY_FAILURE" for c in opp.constraints)


# -----------------------------------------------------------------------------
# Test 7: High Competition Reduces Competition Opportunity
# -----------------------------------------------------------------------------
def test_high_competition_pressure(saree_retail_stage6_payload):
    """
    Competitive pressure 0.85 reduces competition opportunity score to 1 - 0.85 = 0.15.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["competition"] = {
        "competitive_pressure_score": 0.85,
        "competitive_pressure": "HIGH",
        "confidence": 0.85,
        "direct": {"count": 15}
    }

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert opp.component_scores.competition_opportunity.score == pytest.approx(0.15, abs=0.01)


# -----------------------------------------------------------------------------
# Test 8: Missing Demand -> Neutral 0.50 Fallback with Evidence Gap
# -----------------------------------------------------------------------------
def test_missing_demand_neutral_fallback(saree_retail_stage6_payload):
    """
    Missing demand evidence defaults to 0.50 score with low confidence without crashing.
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["demand_evidence"] = {}
    payload["demand_prediction"] = None

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert opp.component_scores.demand.score == 0.50
    assert opp.demand_source.type == DemandSourceType.UNAVAILABLE
    assert opp.component_scores.demand.confidence <= 0.40


# -----------------------------------------------------------------------------
# Test 9: Deterministic Repeatability
# -----------------------------------------------------------------------------
def test_deterministic_repeatability(saree_retail_stage6_payload):
    """
    Executing the engine 10 times with identical input produces identical numerical scores.
    """
    res1 = opportunity_evaluation_engine.evaluate(saree_retail_stage6_payload)
    for _ in range(10):
        res_i = opportunity_evaluation_engine.evaluate(saree_retail_stage6_payload)
        assert res1.opportunity_result.market_opportunity_score == res_i.opportunity_result.market_opportunity_score
        assert res1.opportunity_result.confidence == res_i.opportunity_result.confidence
        assert res1.opportunity_result.level == res_i.opportunity_result.level


# -----------------------------------------------------------------------------
# Test 10: Scores Clamped Between 0.0 and 1.0
# -----------------------------------------------------------------------------
def test_scores_boundary_clamp(saree_retail_stage6_payload):
    """
    All scores must be bounded in [0.0, 1.0].
    """
    payload = dict(saree_retail_stage6_payload)
    payload["market_indicators"]["demand_evidence"]["demand_signal_score"] = 5.0
    payload["market_indicators"]["competition"]["competitive_pressure_score"] = -1.0

    res = opportunity_evaluation_engine.evaluate(payload)
    opp = res.opportunity_result

    assert 0.0 <= opp.market_opportunity_score <= 1.0
    assert 0.0 <= opp.component_scores.demand.score <= 1.0
    assert 0.0 <= opp.component_scores.competition_opportunity.score <= 1.0
    assert 0.0 <= opp.confidence <= 1.0


# -----------------------------------------------------------------------------
# Test 11: Configured Weights Sum to 1.0
# -----------------------------------------------------------------------------
def test_opportunity_weights_sum_to_one():
    """
    OPPORTUNITY_WEIGHTS must sum to 1.0.
    """
    total = sum(OPPORTUNITY_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-6
    assert sum(SUPPLY_WEIGHTS.values()) == pytest.approx(1.0, rel=1e-6)


# -----------------------------------------------------------------------------
# Test 12: Adapter & Orchestrator Stage 7 Skip Behavior
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_orchestrator_adapter_stage7_skip(saree_retail_stage6_payload):
    """
    OpportunityEvaluationAdapter retrieves Stage 6 from state, records Stage 7 skip,
    and returns completed Stage 8 dict.
    """
    adapter = OpportunityEvaluationAdapter()
    state = {
        "analysis_id": "test-orch-id",
        "session_id": "test-orch-sess",
        "agent_results": {
            "market_intelligence_engine": saree_retail_stage6_payload
        },
        "workflow_stages": {}
    }

    result = await adapter.execute(
        business_profile={"business_profile": {"business_id": "saree_retail"}},
        knowledge_context={},
        state=state
    )

    assert result["workflow"]["stage"] == 8
    assert result["workflow"]["state"] == "MARKET_OPPORTUNITY_EVALUATED"
    assert state["workflow_stages"]["stage_7"]["status"] == "SKIPPED"
    assert "opportunity_result" in result


# -----------------------------------------------------------------------------
# Test 13: FastAPI HTTP API Endpoint POST /api/v1/opportunity-evaluation/analyze
# -----------------------------------------------------------------------------
def test_fastapi_opportunity_evaluation_endpoint(saree_retail_stage6_payload):
    """
    FastAPI endpoint POST /api/v1/opportunity-evaluation/analyze returns 200 with schema.
    """
    client = TestClient(app)
    response = client.post(
        "/api/v1/opportunity-evaluation/analyze",
        json=saree_retail_stage6_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["workflow"]["stage"] == 8
    assert "opportunity_result" in data
    assert data["opportunity_result"]["market_opportunity_score"] > 0.80
    assert data["next_stage"]["component"] == "FEASIBILITY_ENGINE"


# -----------------------------------------------------------------------------
# Test 14: FastAPI Health Check Endpoint GET /api/v1/opportunity-evaluation/health
# -----------------------------------------------------------------------------
def test_fastapi_opportunity_evaluation_health():
    """
    FastAPI endpoint GET /api/v1/opportunity-evaluation/health returns 200 with weights and version.
    """
    client = TestClient(app)
    response = client.get("/api/v1/opportunity-evaluation/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["stage"] == 8
    assert "weights" in data


# -----------------------------------------------------------------------------
# Test 15: Distinct Business Test — Poultry Farm in Bangalore South
# -----------------------------------------------------------------------------
def test_distinct_business_poultry_farm():
    """
    Verifies that a Commercial Poultry Farm in Bangalore South evaluates dynamically
    with its own distinct business context, location, analysis_id, and scores.
    """
    poultry_payload = {
        "analysis_id": "poultry-analysis-999",
        "session_id": "poultry-session-999",
        "workflow": {"stage": 6, "state": "MARKET_INTELLIGENCE_ANALYZED", "status": "complete"},
        "business_context": {
            "business_id": "poultry_farm",
            "specific_business": "Broiler Poultry Farm Unit",
            "sector": "Animal Husbandry",
            "nic_code": "01461"
        },
        "location_context": {
            "district": "Bengaluru Urban",
            "state": "Karnataka",
            "country": "India"
        },
        "market_indicators": {
            "demand_evidence": {
                "demand_signal_strength": "STRONG",
                "demand_signal_score": 0.85,
                "confidence": 0.88
            },
            "competition": {
                "competitive_pressure_score": 0.35,
                "competitive_pressure": "MODERATE",
                "confidence": 0.85,
                "direct": {"count": 6}
            },
            "infrastructure": {
                "readiness": "AVAILABLE",
                "readiness_score": 0.90,
                "critical_gaps": [],
                "confidence": 0.85
            },
            "supply_ecosystem": {
                "supply_risk_score": 0.25,
                "critical_input_coverage": {"coverage_ratio": 0.90},
                "accessibility": "HIGH",
                "confidence": 0.80
            },
            "market_access": {
                "geographic_accessibility_score": 0.80,
                "confidence": 0.80
            },
            "market_capacity": {
                "status": "AVAILABLE",
                "net_capacity_score": 0.70,
                "capacity_signal": "EXPANSION_CAPACITY",
                "confidence": 0.75
            },
            "seasonality": {
                "annual_volatility": 0.20,
                "seasonal_risk": "LOW"
            }
        },
        "evidence_quality": {
            "overall_confidence": 0.82,
            "proxy_dependency": 0.30,
            "data_gaps": []
        }
    }

    client = TestClient(app)
    response = client.post("/api/v1/opportunity-evaluation/analyze", json=poultry_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "poultry-analysis-999"
    assert data["business_context"]["business_id"] == "poultry_farm"
    assert data["business_context"]["specific_business"] == "Broiler Poultry Farm Unit"
    assert data["location_context"]["district"] == "Bengaluru Urban"
    # Verify non-saree score
    opp = data["opportunity_result"]
    assert opp["component_scores"]["demand"]["score"] == 0.85
    assert opp["component_scores"]["competition_opportunity"]["score"] == pytest.approx(0.65, abs=0.01)
    assert opp["level"] in [OpportunityLevel.HIGH_OPPORTUNITY, OpportunityLevel.MODERATE_OPPORTUNITY]


# -----------------------------------------------------------------------------
# Test 16: Distinct Business Test — Rice Mill in Mandya
# -----------------------------------------------------------------------------
def test_distinct_business_rice_mill():
    """
    Verifies that a Mini Rice Mill in Mandya evaluates dynamically with distinct values.
    """
    rice_mill_payload = {
        "analysis_id": "rice-mill-analysis-888",
        "session_id": "rice-mill-session-888",
        "workflow": {"stage": 6, "state": "MARKET_INTELLIGENCE_ANALYZED", "status": "complete"},
        "business_context": {
            "business_id": "rice_mill",
            "specific_business": "Mini Rice Mill Processing Unit",
            "sector": "Agro Processing",
            "nic_code": "10612"
        },
        "location_context": {
            "district": "Mandya",
            "state": "Karnataka",
            "country": "India"
        },
        "market_indicators": {
            "demand_evidence": {
                "demand_signal_strength": "MODERATE",
                "demand_signal_score": 0.60,
                "confidence": 0.80
            },
            "competition": {
                "competitive_pressure_score": 0.40,
                "competitive_pressure": "MODERATE",
                "confidence": 0.80,
                "direct": {"count": 4}
            },
            "infrastructure": {
                "readiness": "AVAILABLE",
                "readiness_score": 0.80,
                "critical_gaps": [],
                "confidence": 0.80
            },
            "supply_ecosystem": {
                "supply_risk_score": 0.30,
                "critical_input_coverage": {"coverage_ratio": 0.95},
                "accessibility": "HIGH",
                "confidence": 0.85
            },
            "market_access": {
                "geographic_accessibility_score": 0.70,
                "confidence": 0.75
            },
            "market_capacity": {
                "status": "AVAILABLE",
                "net_capacity_score": 0.60,
                "confidence": 0.75
            },
            "seasonality": {
                "annual_volatility": 0.30,
                "seasonal_risk": "MODERATE"
            }
        },
        "evidence_quality": {
            "overall_confidence": 0.78,
            "proxy_dependency": 0.25,
            "data_gaps": []
        }
    }

    client = TestClient(app)
    response = client.post("/api/v1/opportunity-evaluation/analyze", json=rice_mill_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "rice-mill-analysis-888"
    assert data["business_context"]["business_id"] == "rice_mill"
    assert data["business_context"]["specific_business"] == "Mini Rice Mill Processing Unit"
    assert data["location_context"]["district"] == "Mandya"
    opp = data["opportunity_result"]
    assert opp["component_scores"]["demand"]["score"] == 0.60
    assert opp["component_scores"]["competition_opportunity"]["score"] == pytest.approx(0.60, abs=0.01)
