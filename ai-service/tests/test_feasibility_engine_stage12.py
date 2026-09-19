"""
Test Suite for Stage 12: Feasibility Engine.
Validates:
1. Feature vector normalization and upstream provenance tracking
2. Critical gate hard constraints (DSCR, 3-Phase Power, Market Capacity, Statutory)
3. 4-Pillar deterministic weighted synthesis
4. ML Adapter slot interface & NOT_CONFIGURED graceful fallback
5. Dynamic SWOT generation for YES pathway
6. Pivot Advisor candidate generation for NO/Conditional pathway
7. Full API endpoints (/analyze, /{id}, /{id}/calculation, /pivot-suggestions, /health)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.feasibility import (
    FeasibilityEvaluationRequest,
    FeasibilityAnalysisResponse
)
from app.services.feasibility_engine import (
    feasibility_engine,
    feasibility_feature_vector_builder,
    critical_gates_evaluator,
    feasibility_synthesis_engine,
    dynamic_swot_engine,
    pivot_advisor_engine,
    feasibility_ml_adapter
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_stage8_opportunity():
    return {
        "composite_opportunity_score": 82.5,
        "opportunity_score": 82.5,
        "demand_score": 0.85,
        "competition_opportunity": 0.75,
        "market_accessibility": 0.80,
        "market_capacity": 0.78,
        "confidence": 0.90
    }


@pytest.fixture
def mock_stage9_finance():
    return {
        "dscr": 1.65,
        "debt_service": {"dscr": 1.65},
        "break_even_point_percentage": 52.0,
        "break_even": {"break_even_point_percentage": 52.0},
        "total_project_cost": 500000.0,
        "estimated_financeable_loan": 375000.0,
        "monthly_emi": 8250.0,
        "confidence": 0.92
    }


@pytest.fixture
def mock_stage10_entrepreneur():
    return {
        "readiness_score": 85.0,
        "readiness_level": "HIGH",
        "confidence": 0.88,
        "component_scores": {
            "skills": {"score": 85.0, "status": "STRONG"},
            "experience": {"score": 90.0, "status": "STRONG"},
            "training": {"score": 75.0, "status": "ADEQUATE"},
            "resources": {"score": 85.0, "status": "STRONG"},
            "operational_readiness": {"score": 90.0, "status": "STRONG"}
        },
        "strengths": ["3+ years retail sales experience", "Established supplier contacts"],
        "gaps": []
    }


@pytest.fixture
def mock_stage11_risk():
    return {
        "overall_risk_score": 0.28,
        "overall_risk_severity": "LOW",
        "critical_risks_count": 0,
        "high_risks_count": 0,
        "confidence": 0.89,
        "category_risks": {
            "FINANCIAL": {"score": 0.18, "level": "LOW", "confidence": 0.92},
            "MARKET": {"score": 0.32, "level": "LOW", "confidence": 0.88},
            "OPERATIONAL": {"score": 0.22, "level": "LOW", "confidence": 0.88},
            "SEASONAL": {"score": 0.35, "level": "MEDIUM", "confidence": 0.85},
            "SUPPLY_CHAIN": {"score": 0.25, "level": "LOW", "confidence": 0.85},
            "COMPETITION": {"score": 0.38, "level": "MEDIUM", "confidence": 0.88},
            "INFRASTRUCTURE": {"score": 0.20, "level": "LOW", "confidence": 0.90}
        }
    }


class TestStage12FeasibilityEngine:

    def test_01_complete_viable_saree_retail(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Validates standard viable enterprise with all upstream stages available."""
        req = FeasibilityEvaluationRequest(
            analysis_id="a1111111-1111-1111-1111-111111111111",
            session_id="s1111111-1111-1111-1111-111111111111",
            business_profile={"specific_business": "Traditional Saree Retail", "category": "retail"},
            location_profile={"village": "Bishnupur", "district": "Bankura", "state": "West Bengal"},
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=mock_stage11_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)

        assert isinstance(res, FeasibilityAnalysisResponse)
        assert res.overall_feasibility_score >= 75.0
        assert res.decision in ["VIABLE", "VIABLE_WITH_CAUTION"]
        assert res.recommendation == "YES"
        assert res.confidence_score >= 0.80

        # Check all 4 pillars exist
        assert "market_opportunity" in res.pillar_scores
        assert "financial_viability" in res.pillar_scores
        assert "entrepreneur_readiness" in res.pillar_scores
        assert "risk_resilience" in res.pillar_scores

        # Check Critical Gates
        assert len(res.critical_gates) >= 4
        for gate in res.critical_gates:
            assert gate.status in ["PASS", "CAUTION"]

        # Check Calculation Provenance
        assert len(res.calculation_provenance) >= 4

    def test_02_missing_market_data_reduces_confidence(
        self,
        mock_stage9_finance,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Validates handling when Stage 8 opportunity data is missing."""
        req = FeasibilityEvaluationRequest(
            opportunity_result=None,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=mock_stage11_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        assert res.pillar_scores["market_opportunity"].status in ["DATA_GAP", "ADEQUATE", "CAUTION"]
        assert res.confidence_score <= 0.85

    def test_03_missing_financial_data_triggers_data_insufficient(self):
        """Validates that missing major stages leads to DATA_INSUFFICIENT or reduced confidence."""
        req = FeasibilityEvaluationRequest(
            opportunity_result=None,
            financial_analysis=None,
            entrepreneur_readiness=None,
            risk_analysis=None
        )

        res = feasibility_engine.evaluate_feasibility(req)
        assert res.decision == "DATA_INSUFFICIENT"
        assert res.recommendation == "CONDITIONAL"
        assert res.confidence_score < 0.65

    def test_04_novice_entrepreneur_lower_readiness_pillar(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage11_risk
    ):
        """Validates that a novice entrepreneur with 0 experience gets lower readiness pillar."""
        novice_ent = {
            "readiness_score": 35.0,
            "readiness_level": "DEVELOPING",
            "confidence": 0.85,
            "component_scores": {
                "skills": {"score": 25.0, "status": "GAP"},
                "experience": {"score": 10.0, "status": "GAP"},
                "training": {"score": 50.0, "status": "ADEQUATE"},
                "resources": {"score": 40.0, "status": "GAP"},
                "operational_readiness": {"score": 50.0, "status": "ADEQUATE"}
            }
        }

        req = FeasibilityEvaluationRequest(
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=novice_ent,
            risk_analysis=mock_stage11_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        assert res.pillar_scores["entrepreneur_readiness"].score == 35.0
        assert res.pillar_scores["entrepreneur_readiness"].weighted_contribution == 7.0  # 35 * 0.20
        assert res.decision in ["VIABLE_WITH_CAUTION", "CONDITIONALLY_VIABLE"]

    def test_05_high_competition_and_saturated_market(
        self,
        mock_stage9_finance,
        mock_stage10_entrepreneur
    ):
        """Validates market capacity gate caution when competition is critical."""
        saturated_opp = {
            "composite_opportunity_score": 45.0,
            "demand_score": 0.35,
            "competition_opportunity": 0.30,
            "confidence": 0.85
        }
        saturated_risk = {
            "overall_risk_score": 0.55,
            "overall_risk_severity": "HIGH",
            "category_risks": {
                "COMPETITION": {"score": 0.72, "level": "HIGH", "confidence": 0.90},
                "MARKET": {"score": 0.65, "level": "HIGH", "confidence": 0.88}
            }
        }

        req = FeasibilityEvaluationRequest(
            opportunity_result=saturated_opp,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=saturated_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        mkt_gate = next(g for g in res.critical_gates if g.gate_id == "MARKET_CAPACITY")
        assert mkt_gate.status in ["CAUTION", "RESTRICT"]

    def test_06_dscr_below_threshold_fails_financial_capacity_gate(
        self,
        mock_stage8_opportunity,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Validates that DSCR < 1.15x triggers RESTRICT on Financial Capacity Gate and NOT_FEASIBLE."""
        weak_fin = {
            "dscr": 1.05,
            "debt_service": {"dscr": 1.05},
            "break_even_point_percentage": 78.0,
            "total_project_cost": 800000.0,
            "confidence": 0.90
        }

        req = FeasibilityEvaluationRequest(
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=weak_fin,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=mock_stage11_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        fin_gate = next(g for g in res.critical_gates if g.gate_id == "FINANCIAL_CAPACITY")
        assert fin_gate.status == "RESTRICT"
        assert res.decision == "NOT_FEASIBLE"
        assert res.recommendation == "NO"

    def test_07_power_infrastructure_mismatch_fails_infrastructure_gate(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur
    ):
        """Validates that 3-Phase power mismatch fails critical infrastructure gate."""
        power_mismatch_risk = {
            "overall_risk_score": 0.62,
            "overall_risk_severity": "CRITICAL",
            "category_risks": {
                "INFRASTRUCTURE": {
                    "score": 0.88,
                    "level": "CRITICAL",
                    "drivers": ["Machinery requires 3-phase power, only single phase connected"]
                }
            }
        }

        req = FeasibilityEvaluationRequest(
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=power_mismatch_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        infra_gate = next(g for g in res.critical_gates if g.gate_id == "CRITICAL_INFRASTRUCTURE")
        assert infra_gate.status == "RESTRICT"
        assert res.decision == "NOT_FEASIBLE"
        assert res.recommendation == "NO"

    def test_08_severe_enterprise_risk_lowers_resilience_pillar(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur
    ):
        """Validates that overall risk score of 0.75 inverts to 25.0 resilience score."""
        high_risk = {
            "overall_risk_score": 0.75,
            "overall_risk_severity": "HIGH",
            "confidence": 0.90
        }

        req = FeasibilityEvaluationRequest(
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=high_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        assert res.pillar_scores["risk_resilience"].score == 25.0
        assert res.pillar_scores["risk_resilience"].weighted_contribution == 5.0  # 25 * 0.20

    def test_09_ml_adapter_not_configured_fallback(self):
        """Verifies clean ML adapter fallback without fabricated predictions."""
        res = feasibility_ml_adapter.predict(feasibility_feature_vector_builder.build_feature_vector())
        assert res["status"] == "NOT_CONFIGURED"
        assert res["prediction"] is None
        assert res["probability"] is None

    def test_10_dynamic_swot_generation(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Verifies evidence-grounded Dynamic SWOT contains all 4 quadrants with provenance."""
        req = FeasibilityEvaluationRequest(
            business_profile={"specific_business": "Traditional Saree Retail"},
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=mock_stage11_risk
        )

        res = feasibility_engine.evaluate_feasibility(req)
        swot = res.dynamic_swot

        assert len(swot.strengths) >= 1
        assert len(swot.weaknesses) >= 1
        assert len(swot.opportunities) >= 1
        assert len(swot.threats) >= 1

        # Check evidence links
        assert any("STAGE_9" in s.source_stage for s in swot.strengths)
        assert any("STAGE_8" in o.source_stage for o in swot.opportunities)

    def test_11_pivot_advisor_recommendations(self):
        """Verifies Pivot Advisor produces domain-matched alternative candidates for Saree Retail."""
        vector = feasibility_feature_vector_builder.build_feature_vector(
            financial_data={"total_project_cost": 500000.0},
            entrepreneur_data={"component_scores": {"skills": {"score": 80.0}}}
        )
        pivots = pivot_advisor_engine.recommend_pivots(
            feature_vector=vector,
            business_profile={"specific_business": "Traditional Saree Retail", "category": "retail"}
        )

        assert len(pivots) >= 3
        cand_names = [p.business_name for p in pivots]
        assert any("Tailoring" in n for n in cand_names)
        assert any("Apparel" in n or "Textile" in n for n in cand_names)
        assert all(p.skill_fit_percentage > 70.0 for p in pivots)
        assert all(p.capital_requirement > 0 for p in pivots)

    def test_12_api_feasibility_analyze_endpoint(
        self,
        client,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Integration test for POST /api/v1/feasibility/analyze."""
        payload = {
            "business_profile": {"specific_business": "Dairy Farm Unit", "category": "dairy"},
            "location_profile": {"village": "Arambagh", "district": "Hooghly", "state": "West Bengal"},
            "opportunity_result": mock_stage8_opportunity,
            "financial_analysis": mock_stage9_finance,
            "entrepreneur_readiness": mock_stage10_entrepreneur,
            "risk_analysis": mock_stage11_risk
        }

        response = client.post("/api/v1/feasibility/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "overall_feasibility_score" in data
        assert "decision" in data
        assert "pillar_scores" in data
        assert "critical_gates" in data
        assert "dynamic_swot" in data
        assert "pivot_recommendations" in data

    def test_13_api_feasibility_health_endpoint(self, client):
        """Integration test for GET /api/v1/feasibility/health."""
        response = client.get("/api/v1/feasibility/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["stage"] == 12
        assert "MARKET_OPPORTUNITY" in data["pillars_configured"]

    def test_14_api_pivot_suggestions_endpoint(self, client):
        """Integration test for POST /api/v1/feasibility/pivot-suggestions."""
        payload = {
            "business_profile": {"specific_business": "Spice Grinding Unit", "sector": "food_processing"},
            "available_capital": 300000.0
        }
        response = client.post("/api/v1/feasibility/pivot-suggestions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_15_yes_pathway_unlocks_strategic_dpr_and_swot(
        self,
        mock_stage8_opportunity,
        mock_stage9_finance,
        mock_stage10_entrepreneur,
        mock_stage11_risk
    ):
        """Validates that a viable decision unlocks Strategic SWOT and DPR generation."""
        req = FeasibilityEvaluationRequest(
            business_profile={"specific_business": "Organic Honey Processing", "category": "food_processing"},
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=mock_stage9_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis=mock_stage11_risk
        )
        res = feasibility_engine.evaluate_feasibility(req)
        assert res.recommendation == "YES"
        assert res.decision in ["VIABLE", "VIABLE_WITH_CAUTION"]
        assert len(res.dynamic_swot.strengths) >= 1
        assert len(res.positive_drivers) >= 1

    def test_16_no_pathway_pivot_advisor_alternative_selection_restart(
        self,
        mock_stage8_opportunity,
        mock_stage10_entrepreneur
    ):
        """Validates that a restricted gate (DSCR < 1.15) triggers NOT_FEASIBLE and provides actionable pivot candidates."""
        unviable_finance = {
            "dscr": 0.85,
            "break_even_point_percentage": 88.0,
            "total_project_cost": 900000.0
        }
        req = FeasibilityEvaluationRequest(
            business_profile={"specific_business": "Traditional Saree Retail", "category": "retail"},
            opportunity_result=mock_stage8_opportunity,
            financial_analysis=unviable_finance,
            entrepreneur_readiness=mock_stage10_entrepreneur,
            risk_analysis={"overall_risk_score": 0.70, "overall_risk_severity": "HIGH"}
        )
        res = feasibility_engine.evaluate_feasibility(req)
        assert res.recommendation == "NO"
        assert res.decision == "NOT_FEASIBLE"
        assert len(res.pivot_recommendations) >= 2
        # Verify first pivot candidate has detailed rationale
        p0 = res.pivot_recommendations[0]
        assert p0.skill_fit_percentage > 0.0
        assert p0.capital_requirement < 900000.0
        assert p0.capital_fit in ["WITHIN_BUDGET", "MINIMAL_GAP"]

