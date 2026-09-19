"""
End-to-End Test Suite:
1. Async Orchestrator Execution & Real-Time Polling Status API
2. Stage 12 Feasibility Deterministic Engine as Master Orchestrator Node
3. Multi-Pillar Mathematical Consistency & Critical Constraints Audit
4. Idempotent Execution & Recovery Flow
"""
import pytest
import time
import uuid
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import engine, get_db_context
import app.database.models
from app.main import app as fastapi_app
from app.services.orchestration.orchestrator_service import orchestrator_service
from app.services.feasibility_engine import feasibility_engine
from app.schemas.feasibility import FeasibilityEvaluationRequest

if engine is not None:
    Base.metadata.create_all(bind=engine)

client = TestClient(fastapi_app)


def _setup_full_business_session(text="I want to start a spices manufacturing and packaging unit in Guntur with 6 lakh rupees."):
    """Helper to run Stage 1 -> Stage 2 -> Stage 3."""
    # 1. Intake
    res1 = client.post("/api/v1/intake/text", json={
        "text": text,
        "language_code": "en"
    })
    assert res1.status_code == 200
    session_id = res1.json()["session_id"]

    # 2. Classification
    res2 = client.post("/api/v1/classification/classify", json={
        "session_id": session_id,
        "original_input": text,
        "business_concept": "Spice Grinding & Packaging Unit",
        "language_code": "en",
        "product_service": "Ground Spices",
        "skills": ["grinding", "packaging", "local trade"]
    })
    assert res2.status_code == 200

    # 3. Profile Build
    res3 = client.post("/api/v1/profile/build", json={"session_id": session_id})
    assert res3.status_code == 200
    profile_data = res3.json()
    analysis_id = profile_data["analysis_id"]

    return session_id, analysis_id, profile_data["profile"]


def test_e2e_async_orchestrator_start_and_status_polling():
    """
    Test 1: POST /api/v1/orchestrator/start returns HTTP 202 Accepted.
    GET /api/v1/orchestrator/status/{analysis_id} returns live status.
    """
    session_id, analysis_id, _ = _setup_full_business_session()

    # Step 1: Trigger async start
    res_start = client.post("/api/v1/orchestrator/start", json={
        "session_id": session_id,
        "analysis_id": analysis_id,
        "sync": False
    })
    assert res_start.status_code in [200, 202]
    start_data = res_start.json()
    assert start_data["analysis_id"] == analysis_id
    assert start_data["session_id"] == session_id
    assert start_data["workflow_status"] in ["RUNNING", "COMPLETED"]

    # Step 2: Poll status endpoint
    res_status = client.get(f"/api/v1/orchestrator/status/{analysis_id}")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["analysis_id"] == analysis_id
    assert "progress" in status_data
    assert "completed_stages" in status_data
    assert "workflow_status" in status_data


def test_e2e_synchronous_orchestrator_pipeline_with_stage12():
    """
    Test 2: Full synchronous pipeline execution including Stage 12 Feasibility Engine.
    Verifies that Stage 12 is present in completed agents and results are comprehensive.
    """
    session_id, analysis_id, _ = _setup_full_business_session(
        "I want to start an organic dairy farm in Hassan with 5 lakh rupees."
    )

    res = client.post("/api/v1/orchestrator/start", json={
        "session_id": session_id,
        "analysis_id": analysis_id,
        "sync": True
    })
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["orchestration_status"] == "ORCHESTRATION_COMPLETE"
    assert data["analysis_id"] == analysis_id

    # Verify execution summary includes feasibility_engine (Stage 12)
    summary = data["agent_execution_summary"]
    completed = summary["completed"]
    assert "domain_knowledge_agent" in completed
    assert "market_intelligence_agent" in completed
    assert "market_intelligence_engine" in completed
    assert "opportunity_evaluation_engine" in completed
    assert "finance_engine" in completed
    assert "entrepreneur_profile_engine" in completed
    assert "risk_engine" in completed
    assert "feasibility_engine" in completed

    # Verify Stage 12 Feasibility Output
    results = data["agent_results"]
    assert "feasibility_engine" in results
    feas_res = results["feasibility_engine"]

    assert "overall_feasibility_score" in feas_res
    assert "decision" in feas_res
    assert "recommendation" in feas_res
    assert "pillar_scores" in feas_res
    assert "critical_gates" in feas_res
    assert "calculation_provenance" in feas_res

    # Verify 4 Core Pillars exist
    pillars = feas_res["pillar_scores"]
    assert "market_opportunity" in pillars
    assert "financial_viability" in pillars
    assert "entrepreneur_readiness" in pillars
    assert "risk_resilience" in pillars

    # Mathematical Verification: If critical gate RESTRICT exists, capped at 38.0; otherwise equals sum
    expected_sum = sum(p["weighted_contribution"] for p in pillars.values())
    has_restrict = any(g["status"] == "RESTRICT" for g in feas_res["critical_gates"])
    if has_restrict:
        assert feas_res["overall_feasibility_score"] == min(round(expected_sum, 1), 38.0)
    else:
        assert abs(feas_res["overall_feasibility_score"] - expected_sum) < 0.5


def test_stage12_feasibility_direct_mathematical_consistency():
    """
    Test 3: Direct Stage 12 deterministic synthesis math audit.
    Verify:
    1. Weighted contribution = score * weight for each pillar.
    2. Weights sum to 1.0.
    3. Overall feasibility score equals sum of pillar contributions.
    """
    sample_opp = {
        "opportunity_result": {
            "market_opportunity_score": 0.82,
            "demand_growth_rate": 0.15,
            "competition_intensity_score": 0.40
        }
    }
    sample_fin = {
        "dscr": 1.75,
        "break_even": {"break_even_point_percentage": 42.5},
        "project_financing": {
            "total_project_cost": 500000.0,
            "estimated_financeable_loan": 350000.0,
            "promoter_contribution": 150000.0
        },
        "monthly_emi": 7500.0
    }
    sample_ep = {
        "status": "READY",
        "readiness_score": 85.0,
        "readiness_level": "High",
        "dimension_scores": {
            "skills": 80.0,
            "experience": 85.0,
            "training": 90.0,
            "resources": 85.0,
            "operations": 85.0
        }
    }
    sample_risk = {
        "overall_risk_score": 30.0,
        "overall_risk_severity": "LOW",
        "market_risk": {"score": 25.0, "severity": "LOW"},
        "financial_risk": {"score": 35.0, "severity": "MEDIUM"}
    }

    req = FeasibilityEvaluationRequest(
        analysis_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        business_profile={"specific_business": "Mustard Oil Mill", "category": "Manufacturing"},
        location_profile={"district": "Bharatpur", "state": "Rajasthan"},
        opportunity_result=sample_opp,
        financial_analysis=sample_fin,
        entrepreneur_readiness=sample_ep,
        risk_analysis=sample_risk
    )

    res = feasibility_engine.evaluate_feasibility(req)

    assert res.overall_feasibility_score >= 0 and res.overall_feasibility_score <= 100
    assert res.decision in ["VIABLE", "VIABLE_WITH_CAUTION", "CONDITIONALLY_VIABLE", "NOT_FEASIBLE"]
    assert res.recommendation in ["YES", "CONDITIONAL", "NO"]

    # Pillar checks
    total_weights = 0.0
    calc_sum = 0.0
    for key, pillar in res.pillar_scores.items():
        total_weights += pillar.weight
        expected_contribution = round(pillar.score * pillar.weight, 2)
        assert abs(pillar.weighted_contribution - expected_contribution) < 0.1
        calc_sum += pillar.weighted_contribution

    assert abs(total_weights - 1.0) < 0.01
    assert abs(res.overall_feasibility_score - calc_sum) < 0.5


def test_stage12_feasibility_missing_upstream_data_gap_handling():
    """
    Test 4: Stage 12 handles missing inputs gracefully with DATA_GAP provenance and safe defaults.
    """
    req = FeasibilityEvaluationRequest(
        analysis_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        business_profile={"specific_business": "Handicraft Studio"},
        location_profile={"district": "Jaipur", "state": "Rajasthan"},
        opportunity_result=None,
        financial_analysis=None,
        entrepreneur_readiness=None,
        risk_analysis=None
    )

    res = feasibility_engine.evaluate_feasibility(req)
    assert res.overall_feasibility_score is not None
    assert len(res.pillar_scores) == 4
    assert res.decision in ["DATA_INSUFFICIENT", "NOT_FEASIBLE", "CONDITIONALLY_VIABLE"]
    assert res.recommendation in ["NEEDS_VALIDATION", "NO", "CONDITIONAL"]
    for pillar in res.pillar_scores.values():
        assert pillar.status in ["DATA_GAP", "CAUTION", "RESTRICT", "ADEQUATE"]


def test_orchestrator_idempotency_already_complete():
    """
    Test 5: Running orchestrator twice for same completed analysis returns ALREADY_COMPLETE.
    """
    session_id, analysis_id, _ = _setup_full_business_session(
        "I want to start a pottery workshop in Khurja with 2 lakh rupees."
    )

    # First run (sync)
    res1 = client.post("/api/v1/orchestrator/start", json={
        "session_id": session_id,
        "analysis_id": analysis_id,
        "sync": True
    })
    assert res1.status_code == 200

    # Second run (async start) -> should detect already complete
    res2 = client.post("/api/v1/orchestrator/start", json={
        "session_id": session_id,
        "analysis_id": analysis_id,
        "sync": False,
        "force_refresh": False
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ALREADY_COMPLETE"
    assert data2["progress"] == 100
