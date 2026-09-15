"""
Deterministic Test Suite for Stage 11: Risk Engine.
Validates multi-vector risk synthesis across Market, Financial, Operational,
Seasonal, Supply Chain, Competition, and Infrastructure categories,
including Critical Risk Ceiling enforcement and REST API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.risk_engine import risk_engine
from app.schemas.risk_analysis import RiskAnalysisRequest, RiskAnalysisResponse


@pytest.fixture
def client():
    return TestClient(app)


class TestStage11RiskEngine:
    """
    Focused unit and API verification suite for Stage 11.
    """

    # -------------------------------------------------------------------------
    # Test 1: Healthy Enterprise (Stage 9 DSCR 1.95x, Strong Demand) -> LOW / MEDIUM Risk
    # -------------------------------------------------------------------------
    def test_01_healthy_enterprise_low_risk(self):
        payload = {
            "business_profile": {
                "business_id": "flour_milling_micro",
                "specific_business": "Atta Chakki Unit"
            },
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 1.95,
                    "viability_status": "HIGHLY_VIABLE"
                },
                "break_even_analysis": {
                    "break_even_point_percentage": 42.0
                }
            },
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "HIGH"},
                    "competition_evidence": {"competitor_count": 1}
                }
            },
            "entrepreneur_readiness": {
                "readiness_score": 85.0,
                "gaps": []
            }
        }
        res = risk_engine.analyze(payload)

        assert res.success is True
        assert res.overall_risk_severity in ["LOW", "MEDIUM"]
        assert res.overall_risk_score < 0.45
        assert res.critical_risks_count == 0
        assert res.category_risks["FINANCIAL"].severity == "LOW"
        assert res.category_risks["MARKET"].severity == "LOW"
        assert res.category_risks["OPERATIONAL"].severity == "LOW"

    # -------------------------------------------------------------------------
    # Test 2: Fragile DSCR (< 1.15x) -> CRITICAL Financial Risk
    # -------------------------------------------------------------------------
    def test_02_dscr_below_threshold_triggers_critical_financial_risk(self):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 1.08,
                    "viability_status": "CRITICAL_RISK"
                }
            }
        }
        res = risk_engine.analyze(payload)

        assert res.category_risks["FINANCIAL"].severity == "CRITICAL"
        assert res.category_risks["FINANCIAL"].score >= 0.85
        assert res.critical_risks_count >= 1

    # -------------------------------------------------------------------------
    # Test 3: Critical Risk Ceiling Rule Enforcement
    # -------------------------------------------------------------------------
    def test_03_critical_ceiling_rule_enforcement(self):
        # Even if all other categories are mild, a single CRITICAL risk MUST guarantee HIGH/CRITICAL overall severity
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 1.02  # CRITICAL
                }
            },
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "VERY_HIGH"},
                    "competition_evidence": {"competitor_count": 0}
                }
            },
            "entrepreneur_readiness": {
                "readiness_score": 95.0
            }
        }
        res = risk_engine.analyze(payload)

        assert res.overall_risk_severity in ["HIGH", "CRITICAL"]
        assert res.provenance.critical_ceiling_applied is True
        assert res.overall_risk_score >= 0.65

    # -------------------------------------------------------------------------
    # Test 4: High Break-Even Point (> 70%) Elevates Risk
    # -------------------------------------------------------------------------
    def test_04_high_break_even_point_elevates_financial_risk(self):
        payload = {
            "business_profile": {"business_id": "oil_expeller_unit"},
            "financial_analysis": {
                "financial_viability": {"debt_service_coverage_ratio": 1.45},
                "break_even_analysis": {"break_even_point_percentage": 78.5}
            }
        }
        res = risk_engine.analyze(payload)
        fin = res.category_risks["FINANCIAL"]

        assert any("break-even" in d.lower() for d in fin.drivers)
        assert fin.score >= 0.50

    # -------------------------------------------------------------------------
    # Test 5: Subdued Market Demand -> HIGH Market Risk
    # -------------------------------------------------------------------------
    def test_05_market_demand_low_triggers_high_market_risk(self):
        payload = {
            "business_profile": {"business_id": "spice_grinding_packaging"},
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "LOW"}
                }
            }
        }
        res = risk_engine.analyze(payload)
        mkt = res.category_risks["MARKET"]

        assert mkt.severity == "HIGH"
        assert mkt.score >= 0.70

    # -------------------------------------------------------------------------
    # Test 6: Operational Risk Derived from Stage 10 Readiness Gaps
    # -------------------------------------------------------------------------
    def test_06_operational_risk_derived_from_stage10_readiness_gaps(self):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "entrepreneur_readiness": {
                "readiness_score": 35.0,
                "gaps": [
                    {"dimension": "SKILLS", "gap_description": "Lack of machine maintenance skills"}
                ]
            }
        }
        res = risk_engine.analyze(payload)
        ops = res.category_risks["OPERATIONAL"]

        assert ops.severity == "HIGH"
        assert ops.score >= 0.70
        assert any("maintenance" in d.lower() for d in ops.drivers)

    # -------------------------------------------------------------------------
    # Test 7: Agri-Processing Seasonal Exposure
    # -------------------------------------------------------------------------
    def test_07_seasonal_agri_processing_exposure(self):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"}
        }
        res = risk_engine.analyze(payload)
        sea = res.category_risks["SEASONAL"]

        assert sea.severity == "MEDIUM"
        assert any("crop" in d.lower() or "rabi" in d.lower() for d in sea.drivers)

    # -------------------------------------------------------------------------
    # Test 8: Perishable Dairy Supply Chain Risk
    # -------------------------------------------------------------------------
    def test_08_perishable_dairy_supply_chain_risk(self):
        payload = {
            "business_profile": {"business_id": "dairy_micro_chilling_aggregator"}
        }
        res = risk_engine.analyze(payload)
        sup = res.category_risks["SUPPLY_CHAIN"]

        assert sup.severity == "HIGH"
        assert any("perishable" in d.lower() or "cold chain" in d.lower() for d in sup.drivers)

    # -------------------------------------------------------------------------
    # Test 9: Competitor Clustering Risk
    # -------------------------------------------------------------------------
    def test_09_competitor_clustering_density_risk(self):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "market_intelligence": {
                "market_indicators": {
                    "competition_evidence": {"competitor_count": 7}
                }
            }
        }
        res = risk_engine.analyze(payload)
        comp = res.category_risks["COMPETITION"]

        assert comp.severity == "HIGH"
        assert comp.score >= 0.70

    # -------------------------------------------------------------------------
    # Test 10: Single-Phase Domestic Power for 3-Phase Machine -> CRITICAL
    # -------------------------------------------------------------------------
    def test_10_missing_3phase_power_triggers_critical_infrastructure_risk(self):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "entrepreneur_readiness": {
                "resources": {
                    "power_connection_type": "SINGLE_PHASE"
                }
            }
        }
        res = risk_engine.analyze(payload)
        inf = res.category_risks["INFRASTRUCTURE"]

        assert inf.severity == "CRITICAL"
        assert inf.score >= 0.85
        assert res.critical_risks_count >= 1

    # -------------------------------------------------------------------------
    # Test 11: Missing Upstream Evidence Defaults Safely with Confidence Score
    # -------------------------------------------------------------------------
    def test_11_missing_evidence_defaults_safely(self):
        payload = {
            "business_profile": {"business_id": "handloom_weaving_unit"}
        }
        res = risk_engine.analyze(payload)

        assert res.success is True
        assert len(res.category_risks) == 7
        assert 0.0 <= res.overall_risk_score <= 1.0
        assert res.confidence >= 0.60

    # -------------------------------------------------------------------------
    # Test 12: REST API POST /api/v1/risk-analysis/analyze
    # -------------------------------------------------------------------------
    def test_12_api_risk_analyze_endpoint(self, client):
        payload = {
            "business_profile": {"business_id": "flour_milling_micro"},
            "financial_analysis": {
                "financial_viability": {"debt_service_coverage_ratio": 1.70}
            }
        }
        response = client.post("/api/v1/risk-analysis/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "category_risks" in data
        assert len(data["category_risks"]) == 7

    # -------------------------------------------------------------------------
    # Test 13: REST API GET /api/v1/risk-analysis/health
    # -------------------------------------------------------------------------
    def test_13_api_risk_health_endpoint(self, client):
        response = client.get("/api/v1/risk-analysis/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["stage"] == 11
        assert data["critical_ceiling_rule"] == "ENABLED"
