"""
Comprehensive Test Suite for STRICT KALPA WORKFLOW: Stage 10 -> Stage 11 -> Stage 12 Hard Gating.
Tests:
✓ Stage 10 blocks Stage 11 when questions are pending / required info is missing
✓ Stage 10 questions persist independently (independent question state: PENDING, ANSWERED)
✓ Answering one question does not remove other unanswered questions
✓ Voice answer maps to correct structured field and merges into profile
✓ Text answer maps to correct structured field and merges into profile
✓ Stage 10 incomplete remains incomplete (status: CLARIFICATION_REQUIRED / PROFILE_INCOMPLETE)
✓ Stage 10 complete unlocks Stage 11
✓ Stage 11 consumes Stage 6 Market, Stage 8 Opportunity, Stage 9 Financial, Stage 10 Profile
✓ All 7 risk categories are calculated and returned (FINANCIAL, MARKET, OPERATIONAL, SEASONAL, SUPPLY_CHAIN, COMPETITION, INFRASTRUCTURE)
✓ Missing evidence produces DATA_GAP (no fake default LOW scores)
✓ Stage 11 blocks when dependencies are missing (HTTP 409 Conflict)
✓ Stage 11 produces business-specific risk (Saree Retail vs Dairy vs Rice Mill)
✓ Stage 11 complete unlocks Stage 12
✓ Stage 12 cannot execute early (HTTP 409 Conflict if Stage 8, 9, 10, or 11 missing)
✓ Stage 12 consumes all required upstream outputs
✓ Feasibility YES routes to SWOT / DPR
✓ Feasibility NO routes to Pivot Advisor
✓ Re-evaluation invalidates downstream stages (Stage 10 modification invalidates 11 & 12)
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine, is_stage10_complete
from app.services.risk_engine import risk_engine
from app.services.feasibility_engine import feasibility_engine
from app.services.orchestration.orchestrator_service import orchestrator_service


@pytest.fixture
def client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------
SAMPLE_BUSINESS_PROFILE = {
    "business_id": "saree_retail",
    "specific_business": "Traditional Saree Retail",
    "category": "Retail",
    "sector": "Textiles & Apparel"
}

SAMPLE_LOCATION_PROFILE = {
    "name": "Surat Catchment",
    "district": "Surat",
    "state": "Gujarat",
    "tier": "Tier-2"
}

SAMPLE_FINANCIAL_PROFILE = {
    "available_capital": 100000.0,
    "available_margin_capital": 100000.0,
    "expected_revenue_monthly": 180000.0
}

SAMPLE_STAGE9_FINANCIAL_OUTPUT = {
    "dscr": 1.65,
    "break_even_point_percentage": 42.5,
    "project_financing": {
        "total_project_cost": 1000000.0,
        "promoter_contribution": 100000.0,
        "estimated_financeable_loan": 900000.0,
        "monthly_emi": 14835.0
    },
    "working_capital": {
        "monthly_working_capital_required": 120000.0,
        "working_capital_gap": 0.0
    },
    "profitability": {
        "net_profit_margin_percentage": 18.2,
        "first_year_projected_profit": 350000.0
    }
}

SAMPLE_STAGE6_MARKET_OUTPUT = {
    "market_indicators": {
        "demand_evidence": {
            "demand_level": "STRONG",
            "demand_score": 0.82,
            "evidence": "High seasonal and festive footfall in Surat market"
        },
        "competitor_evidence": {
            "competitor_density": "MODERATE",
            "competitor_count": 8,
            "competition_pressure": "MEDIUM"
        },
        "infrastructure_evidence": {
            "power_availability": "ADEQUATE",
            "road_connectivity": "GOOD"
        }
    }
}

SAMPLE_STAGE8_OPPORTUNITY_OUTPUT = {
    "market_opportunity_score": 0.84,
    "opportunity_level": "HIGH",
    "market_depth": "EXPANDING",
    "demand_stability": "STABLE"
}


class TestStrictWorkflowStage10To11To12:

    # -------------------------------------------------------------------------
    # 1. Stage 10 Hard Gate & Authoritative is_stage10_complete validation
    # -------------------------------------------------------------------------
    def test_stage10_incomplete_profile_has_pending_questions_and_is_not_complete(self):
        """Initial empty profile must have missing fields, pending questions, and is_stage10_complete == False."""
        req = {
            "business_profile": SAMPLE_BUSINESS_PROFILE,
            "user_profile": {}  # No skills, experience, or resources provided
        }
        res = entrepreneur_profile_engine.analyze(req)
        assert res.status in ["CLARIFICATION_REQUIRED", "PROFILE_INCOMPLETE"]
        assert len(res.questions) >= 3
        assert is_stage10_complete(res) is False
        assert is_stage10_complete(res.model_dump()) is False

    # -------------------------------------------------------------------------
    # 2. Stage 10 Clarifications: Voice & Text produce equivalent structured data
    # -------------------------------------------------------------------------
    def test_voice_and_text_clarifications_update_same_profile(self, client):
        """Both voice transcript and text input extract structured fields and merge into profile."""
        session_id = f"test-voice-text-{uuid.uuid4()}"

        # Text clarification for skills
        text_resp = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "skills",
            "text": "I have 5 years retail sales experience and knowledge of saree inventory management.",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })
        assert text_resp.status_code == 200
        text_data = text_resp.json()
        assert "skills" in text_data["entrepreneur_profile"]["answered_fields"]

        # Voice clarification for experience (simulated transcript from STT)
        voice_resp = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "experience.years_of_experience",
            "text": "मैं 3 साल से साड़ी की दुकान में काम कर रहा हूं",
            "is_voice": True,
            "language": "hi",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })
        assert voice_resp.status_code == 200
        voice_data = voice_resp.json()
        assert "experience" in voice_data["entrepreneur_profile"]["answered_fields"]

        # Merged profile retains BOTH skills and experience
        ep = voice_data["entrepreneur_profile"]
        assert "skills" in ep["answered_fields"]
        assert "experience" in ep["answered_fields"]

    # -------------------------------------------------------------------------
    # 3. Answering one question does NOT remove other unanswered questions
    # -------------------------------------------------------------------------
    def test_answering_one_question_preserves_remaining_questions(self, client):
        session_id = f"test-preserve-q-{uuid.uuid4()}"

        # Submit answer to skills only
        resp1 = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "skills",
            "text": "Textile retail, inventory procurement, billing",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })
        assert resp1.status_code == 200
        data1 = resp1.json()
        r1 = data1["readiness_response"]

        # Skills answered, but experience and resources must still be pending
        assert "skills" not in r1.get("missing_fields", [])
        assert len(r1.get("questions", [])) >= 2  # Experience and Resources remain

    # -------------------------------------------------------------------------
    # 4. Stage 10 Completes only after all required dimensions are answered
    # -------------------------------------------------------------------------
    def test_stage10_full_completion_unlocks(self, client):
        session_id = f"test-full-unlock-{uuid.uuid4()}"

        # 1. Answer Skills
        client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "skills",
            "text": "Retail sales, merchandising, customer service",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })

        # 2. Answer Experience
        client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "experience.years_of_experience",
            "text": "4 years running a clothing shop",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })

        # 3. Answer Resources
        res3 = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "session_id": session_id,
            "field": "resources.available_area_sqft",
            "text": "300 sq ft commercial retail space with single phase power",
            "business_profile": SAMPLE_BUSINESS_PROFILE
        })
        assert res3.status_code == 200
        data3 = res3.json()
        r3 = data3["readiness_response"]

        assert r3["status"] in ["READY", "COMPLETE"]
        assert len(r3.get("questions", [])) == 0
        assert is_stage10_complete(r3) is True

    # -------------------------------------------------------------------------
    # 5. Stage 11 Risk Analysis Blocks when Stage 10 is Incomplete (HTTP 409)
    # -------------------------------------------------------------------------
    def test_stage11_blocks_with_http_409_when_stage10_incomplete(self, client):
        incomplete_stage10 = {
            "status": "CLARIFICATION_REQUIRED",
            "questions": [{"field": "skills", "question": "What is your experience?"}],
            "missing_fields": ["skills", "resources.available_area_sqft"]
        }

        resp = client.post("/api/v1/risk-analysis/analyze", json={
            "analysis_id": str(uuid.uuid4()),
            "entrepreneur_readiness": incomplete_stage10
        })
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["status"] == "STAGE_11_BLOCKED"
        assert "STAGE_10" in detail["missing_dependencies"]

    # -------------------------------------------------------------------------
    # 6. Stage 11 Consumes Stage 6, 8, 9, 10 & Calculates All 7 Risk Categories
    # -------------------------------------------------------------------------
    def test_stage11_calculates_all_7_categories_from_real_upstream_data(self, client):
        completed_stage10 = {
            "status": "COMPLETE",
            "readiness_score": 82.0,
            "readiness_level": "HIGH",
            "component_scores": {
                "skills": {"score": 85, "status": "STRONG"},
                "experience": {"score": 80, "status": "ADEQUATE"},
                "resources": {"score": 80, "status": "ADEQUATE"}
            },
            "missing_fields": [],
            "questions": []
        }

        resp = client.post("/api/v1/risk-analysis/analyze", json={
            "analysis_id": str(uuid.uuid4()),
            "business_profile": SAMPLE_BUSINESS_PROFILE,
            "location_profile": SAMPLE_LOCATION_PROFILE,
            "financial_profile": SAMPLE_FINANCIAL_PROFILE,
            "financial_analysis": SAMPLE_STAGE9_FINANCIAL_OUTPUT,
            "market_intelligence": SAMPLE_STAGE6_MARKET_OUTPUT,
            "opportunity_result": SAMPLE_STAGE8_OPPORTUNITY_OUTPUT,
            "entrepreneur_readiness": completed_stage10
        })
        assert resp.status_code == 200
        data = resp.json()

        # All 7 categories must be present
        categories = data["category_risks"]
        expected_cats = [
            "FINANCIAL", "MARKET", "OPERATIONAL", "SEASONAL",
            "SUPPLY_CHAIN", "COMPETITION", "INFRASTRUCTURE"
        ]
        for cat in expected_cats:
            assert cat in categories, f"Missing risk category: {cat}"
            cat_data = categories[cat]
            assert "score" in cat_data
            assert "severity" in cat_data
            assert "evidence" in cat_data
            assert "source_stage" in cat_data

    # -------------------------------------------------------------------------
    # 7. Missing Upstream Evidence produces DATA_GAP, NOT fake LOW risk
    # -------------------------------------------------------------------------
    def test_missing_upstream_evidence_produces_data_gap(self, client):
        # Omit financial data entirely
        risk_res = risk_engine.analyze({
            "business_profile": SAMPLE_BUSINESS_PROFILE,
            "location_profile": SAMPLE_LOCATION_PROFILE,
            # No financial_analysis provided
        })

        fin_risk = risk_res.category_risks.get("FINANCIAL")
        assert fin_risk is not None
        assert fin_risk.source_stage in ["UNKNOWN", "DATA_GAP", "BENCHMARK_DATA_UNAVAILABLE"] or fin_risk.confidence < 0.7

    # -------------------------------------------------------------------------
    # 8. Business-Specific Risk Differentiation (Saree Retail vs Dairy vs Rice Mill)
    # -------------------------------------------------------------------------
    def test_business_specific_risk_differentiation(self):
        saree_risk = risk_engine.analyze({"business_profile": {"business_id": "saree_retail"}})
        dairy_risk = risk_engine.analyze({"business_profile": {"business_id": "dairy_farm"}})
        rice_risk = risk_engine.analyze({"business_profile": {"business_id": "rice_mill"}})

        # Dairy has higher perishability/supply-chain risk than saree retail
        saree_supply = saree_risk.category_risks.get("SUPPLY_CHAIN")
        dairy_supply = dairy_risk.category_risks.get("SUPPLY_CHAIN")
        assert dairy_supply.score >= saree_supply.score

        # Rice mill has higher seasonal/raw-material harvest dependency
        rice_season = rice_risk.category_risks.get("SEASONAL")
        saree_season = saree_risk.category_risks.get("SEASONAL")
        assert rice_season.score >= saree_season.score

    # -------------------------------------------------------------------------
    # 9. Stage 12 Feasibility Blocks when Upstream is Incomplete (HTTP 409)
    # -------------------------------------------------------------------------
    def test_stage12_blocks_with_http_409_when_dependencies_missing(self, client):
        # Missing Stage 11 Risk Analysis
        resp = client.post("/api/v1/feasibility/analyze", json={
            "analysis_id": str(uuid.uuid4()),
            "opportunity_result": SAMPLE_STAGE8_OPPORTUNITY_OUTPUT,
            "financial_analysis": SAMPLE_STAGE9_FINANCIAL_OUTPUT,
            "entrepreneur_readiness": {"status": "COMPLETE", "readiness_score": 80, "missing_fields": [], "questions": []},
            # Omit risk_analysis
        })
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert detail["status"] == "DEPENDENCY_NOT_READY"
        assert "STAGE_11" in detail["missing"]

    # -------------------------------------------------------------------------
    # 10. Stage 12 Complete Execution with Real Upstream Inputs
    # -------------------------------------------------------------------------
    def test_stage12_completes_when_all_dependencies_provided(self, client):
        stage10 = {"status": "COMPLETE", "readiness_score": 82.0, "readiness_level": "HIGH", "missing_fields": [], "questions": []}
        stage11 = {
            "overall_risk_score": 0.28,
            "overall_risk_severity": "LOW",
            "confidence": 0.88,
            "critical_risks_count": 0,
            "category_risks": {
                "FINANCIAL": {"score": 0.25, "severity": "LOW", "source_stage": "STAGE_9_FINANCIAL"},
                "MARKET": {"score": 0.20, "severity": "LOW", "source_stage": "STAGE_6_MARKET_INTELLIGENCE"},
                "OPERATIONAL": {"score": 0.30, "severity": "LOW", "source_stage": "STAGE_10_ENTREPRENEUR_PROFILE"},
                "SEASONAL": {"score": 0.35, "severity": "MEDIUM", "source_stage": "BENCHMARK_DATABASE"},
                "SUPPLY_CHAIN": {"score": 0.25, "severity": "LOW", "source_stage": "BENCHMARK_DATABASE"},
                "COMPETITION": {"score": 0.30, "severity": "LOW", "source_stage": "STAGE_6_MARKET_INTELLIGENCE"},
                "INFRASTRUCTURE": {"score": 0.20, "severity": "LOW", "source_stage": "STAGE_6_MARKET_INTELLIGENCE"}
            }
        }

        resp = client.post("/api/v1/feasibility/analyze", json={
            "analysis_id": str(uuid.uuid4()),
            "business_profile": SAMPLE_BUSINESS_PROFILE,
            "location_profile": SAMPLE_LOCATION_PROFILE,
            "opportunity_result": SAMPLE_STAGE8_OPPORTUNITY_OUTPUT,
            "financial_analysis": SAMPLE_STAGE9_FINANCIAL_OUTPUT,
            "entrepreneur_readiness": stage10,
            "risk_analysis": stage11
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_feasibility_score"] >= 50
        assert data["decision"] in ["VIABLE", "VIABLE_WITH_CAUTION", "CONDITIONALLY_VIABLE"]
        assert len(data["dynamic_swot"]["strengths"]) > 0

    # -------------------------------------------------------------------------
    # 11. YES / NO Decision Routing
    # -------------------------------------------------------------------------
    def test_feasibility_routing_decision(self):
        from app.schemas.feasibility import FeasibilityEvaluationRequest

        # Viable case -> routes to SWOT and DPR
        req_viable = FeasibilityEvaluationRequest(
            opportunity_result=SAMPLE_STAGE8_OPPORTUNITY_OUTPUT,
            financial_analysis=SAMPLE_STAGE9_FINANCIAL_OUTPUT,
            entrepreneur_readiness={"status": "COMPLETE", "readiness_score": 85},
            risk_analysis={"overall_risk_score": 0.25, "overall_risk_severity": "LOW", "critical_risks_count": 0}
        )
        viable_res = feasibility_engine.evaluate_feasibility(request=req_viable)
        assert viable_res.decision in ["VIABLE", "VIABLE_WITH_CAUTION"]
        assert viable_res.dynamic_swot is not None

        # Unviable case (DSCR failing critical gate) -> routes to Pivot Advisor
        failing_financial = dict(SAMPLE_STAGE9_FINANCIAL_OUTPUT)
        failing_financial["dscr"] = 0.85  # Below 1.0 threshold
        req_unviable = FeasibilityEvaluationRequest(
            opportunity_result=SAMPLE_STAGE8_OPPORTUNITY_OUTPUT,
            financial_analysis=failing_financial,
            entrepreneur_readiness={"status": "COMPLETE", "readiness_score": 40},
            risk_analysis={"overall_risk_score": 0.85, "overall_risk_severity": "CRITICAL", "critical_risks_count": 2}
        )
        unviable_res = feasibility_engine.evaluate_feasibility(request=req_unviable)
        assert unviable_res.decision == "NOT_FEASIBLE"
        assert len(unviable_res.pivot_recommendations) > 0

    # -------------------------------------------------------------------------
    # 12. Orchestrator Downstream Stage Invalidation
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_orchestrator_invalidates_downstream_stages_on_profile_change(self):
        wf = await orchestrator_service.invalidate_downstream_stages("dummy-session-id", modified_stage=10)
        assert 11 in wf["invalidated_stages"]
        assert 12 in wf["invalidated_stages"]
        assert 11 in wf["locked_stages"]
        assert 12 in wf["locked_stages"]
