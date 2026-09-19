"""
KALPA Stage 10-11 Final Robustness Integration Test Suite:
Tests the complete multi-question clarification progression, answer persistence,
Stage 6/8/9/10 evidence consumption in Stage 11, business context differentiation,
and the authoritative workflow context contract.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.services.risk_engine import risk_engine
from app.services.risk_engine.adapters import (
    MarketRiskInputAdapter,
    OpportunityRiskInputAdapter,
    FinancialRiskInputAdapter,
    EntrepreneurProfileRiskInputAdapter
)


@pytest.fixture
def client():
    return TestClient(app)


class TestStage10Stage11RobustnessIntegration:

    # -------------------------------------------------------------------------
    # 1. Multi-Question Step-by-Step Retention Test (Requirement 22)
    # -------------------------------------------------------------------------
    def test_step_by_step_clarification_retention(self, client):
        """
        Initial state: 3 missing fields (skills, experience, resources).
        - Answer skills -> skills answered, experience & resources remain pending.
        - Answer experience -> skills & experience answered, resources remains pending.
        - Answer resources -> all 3 answered, profile becomes READY, no pending questions.
        """
        test_aid = "test-retention-session-901"

        # Step 0: Initial evaluation
        initial_payload = {
            "analysis_id": test_aid,
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Saree Retail",
                "category": "Retail"
            },
            "user_profile": {}  # All missing
        }
        res0 = entrepreneur_profile_engine.analyze(initial_payload)
        assert res0.status == "PROFILE_INCOMPLETE"
        assert "skills" in res0.missing_fields
        assert "experience.years_of_experience" in res0.missing_fields
        assert "resources.available_area_sqft" in res0.missing_fields
        assert len(res0.questions) >= 3

        # Step 1: Submit Q1 (Skills only)
        q1_resp = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "analysis_id": test_aid,
            "text": "I have experience in customer sales and saree fabric presentation.",
            "field": "skills",
            "business_context": {"business_id": "saree_retail"}
        })
        assert q1_resp.status_code == 200
        d1 = q1_resp.json()
        assert d1["success"] is True
        r1 = d1["readiness_evaluation"]
        assert "skills" not in r1["missing_fields"]
        assert "experience.years_of_experience" in r1["missing_fields"]
        assert "resources.available_area_sqft" in r1["missing_fields"]
        assert r1["status"] == "PROFILE_INCOMPLETE"
        assert len(r1["questions"]) >= 2

        # Step 2: Submit Q2 (Experience only)
        q2_resp = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "analysis_id": test_aid,
            "text": "I have 4 years of retail sales experience.",
            "field": "experience.years_of_experience",
            "business_context": {"business_id": "saree_retail"}
        })
        assert q2_resp.status_code == 200
        d2 = q2_resp.json()
        assert d2["success"] is True
        r2 = d2["readiness_evaluation"]
        assert "skills" not in r2["missing_fields"]
        assert "experience.years_of_experience" not in r2["missing_fields"]
        assert "resources.available_area_sqft" in r2["missing_fields"]
        assert r2["status"] == "PROFILE_INCOMPLETE"
        assert len(r2["questions"]) >= 1

        # Step 3: Submit Q3 (Resources only)
        q3_resp = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "analysis_id": test_aid,
            "text": "I have a commercial shop of 350 sq ft available on main road.",
            "field": "resources.available_area_sqft",
            "business_context": {"business_id": "saree_retail"}
        })
        assert q3_resp.status_code == 200
        d3 = q3_resp.json()
        assert d3["success"] is True
        r3 = d3["readiness_evaluation"]
        assert len(r3["missing_fields"]) == 0
        assert r3["status"] == "READY"
        assert r3["readiness_score"] >= 70.0
        assert len(r3["questions"]) == 0

    # -------------------------------------------------------------------------
    # 2. Stage 11 consumes Stage 6 & Stage 8 Normalized Evidence (Requirement 7, 8, 9, 10, 11)
    # -------------------------------------------------------------------------
    def test_stage11_consumes_stage6_and_stage8_evidence(self):
        """
        Verifies that Stage 11 Risk Engine extracts Stage 6 demand and Stage 8 opportunity score
        and produces real, traceable risk scores without DATA_GAP or BENCHMARK_DATA_UNAVAILABLE.
        """
        payload = {
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Saree Retail"
            },
            # Stage 6 Output
            "market_intelligence": {
                "market_evidence": {
                    "demand_indicators": [
                        {"indicator_name": "catchment_demand", "value": "HIGH", "category": "general"}
                    ],
                    "competitors": {
                        "total_found": 3,
                        "direct": [{"business_name": "Varanasi Sarees", "category": "Retail"}]
                    },
                    "supply_access": [
                        {"hub_name": "Surat Textile Hub", "distance_km": 15.0, "accessibility_rating": "high"}
                    ],
                    "seasonality_evidence": [
                        {"factor_name": "Festive Wedding Season", "peak_months": ["Oct", "Nov", "Dec"]}
                    ],
                    "infrastructure": [
                        {"infrastructure_type": "electricity", "status": "available", "reliability_hours_daily": 20.0}
                    ]
                }
            },
            # Stage 8 Output
            "opportunity_evaluation": {
                "opportunity_result": {
                    "market_opportunity_score": 0.82,
                    "level": "HIGH",
                    "component_scores": {
                        "demand": {"score": 0.85},
                        "competition_opportunity": {"score": 0.78, "direct_competitors": 3},
                        "infrastructure": {"score": 0.90},
                        "supply_ecosystem": {"score": 0.88}
                    }
                }
            },
            # Stage 9 Output
            "financial_analysis": {
                "debt_service": {"dscr": 1.85},
                "break_even": {"break_even_point_percentage": 42.0}
            },
            # Stage 10 Output
            "entrepreneur_readiness": {
                "readiness_score": 82.0,
                "status": "READY",
                "gaps": []
            }
        }

        res = risk_engine.analyze(payload)
        assert res.success is True

        # Market Risk: Consumed Stage 6 + Stage 8
        mkt_risk = res.category_risks["MARKET"]
        assert mkt_risk.severity == "LOW"
        assert mkt_risk.score < 0.35
        assert mkt_risk.source_stage in ["STAGE_6_MARKET_INTELLIGENCE", "STAGE_8_OPPORTUNITY_EVALUATION"]
        assert "missing" not in mkt_risk.formula.lower()

        # Competition Risk: Consumed Stage 6 competitor count (3 units)
        comp_risk = res.category_risks["COMPETITION"]
        assert comp_risk.severity in ["LOW", "MEDIUM"]
        assert comp_risk.source_stage in ["STAGE_6_MARKET_INTELLIGENCE", "STAGE_8_OPPORTUNITY_EVALUATION"]
        assert "3" in str(comp_risk.inputs.get("competitor_count"))

        # Financial Risk: Consumed Stage 9 DSCR 1.85x
        fin_risk = res.category_risks["FINANCIAL"]
        assert fin_risk.severity == "LOW"
        assert fin_risk.source_stage == "STAGE_9_FINANCIAL"

        # Operational Risk: Consumed Stage 10
        ops_risk = res.category_risks["OPERATIONAL"]
        assert ops_risk.severity == "LOW"
        assert ops_risk.source_stage == "STAGE_10_ENTREPRENEUR_PROFILE"

        # All 7 categories populated
        for cat in ["FINANCIAL", "MARKET", "OPERATIONAL", "SEASONAL", "SUPPLY_CHAIN", "COMPETITION", "INFRASTRUCTURE"]:
            assert cat in res.category_risks
            assert res.category_risks[cat].severity != "UNKNOWN"

    # -------------------------------------------------------------------------
    # 3. Contextual Differentiation: Saree Retail vs Dairy Micro-Chilling (Requirement 21)
    # -------------------------------------------------------------------------
    def test_contextual_differentiation_saree_vs_dairy(self):
        """
        Tests that risk scores materially differ between a dry retail business (Saree Retail)
        and a perishable cold-chain business (Dairy Micro-Chilling) under identical conditions.
        """
        # Saree Retail
        saree_payload = {
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "market_intelligence": {
                "market_evidence": {
                    "demand_indicators": [{"indicator_name": "demand", "value": "HIGH"}],
                    "competitors": {"total_found": 2}
                }
            }
        }
        saree_res = risk_engine.analyze(saree_payload)

        # Dairy Micro-Chilling
        dairy_payload = {
            "business_profile": {"business_id": "dairy_micro_chilling_aggregator", "specific_business": "Dairy Micro-Chilling"},
            "market_intelligence": {
                "market_evidence": {
                    "demand_indicators": [{"indicator_name": "demand", "value": "HIGH"}],
                    "competitors": {"total_found": 2}
                }
            }
        }
        dairy_res = risk_engine.analyze(dairy_payload)

        # Supply chain risk for perishable dairy must be significantly higher than dry saree retail
        assert dairy_res.category_risks["SUPPLY_CHAIN"].severity == "HIGH"
        assert saree_res.category_risks["SUPPLY_CHAIN"].severity == "LOW"
        assert dairy_res.category_risks["SUPPLY_CHAIN"].score > saree_res.category_risks["SUPPLY_CHAIN"].score

    # -------------------------------------------------------------------------
    # 4. Authoritative Workflow Context Endpoint Contract (Requirement 1)
    # -------------------------------------------------------------------------
    def test_authoritative_workflow_context_endpoint(self, client):
        """
        Verifies that GET /api/v1/orchestrator/workflow-context/{identifier}
        returns structured canonical context.
        """
        test_id = "00000000-0000-0000-0000-000000000001"
        resp = client.get(f"/api/v1/orchestrator/workflow-context/{test_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "analysis_id" in data
        assert "business_context" in data
        assert "stage6_market_intelligence" in data
        assert "stage8_opportunity_evaluation" in data
        assert "stage9_financial_analysis" in data
        assert "stage10_entrepreneur_profile" in data
        assert "stage11_risk_analysis" in data
