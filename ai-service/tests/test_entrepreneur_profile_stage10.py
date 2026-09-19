"""
Deterministic Test Suite for Stage 10: Entrepreneur Profile Engine.
Validates skill alignment, experience thresholds, training readiness,
power & resource adequacy, operational commitment, incomplete profile clarification,
multilingual fact extraction, and REST API contracts.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.entrepreneur_profile_engine import (
    entrepreneur_profile_engine,
    clarification_extractor,
)
from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestStage10EntrepreneurProfileEngine:
    """
    Focused unit and API verification suite for Stage 10.
    """

    # -------------------------------------------------------------------------
    # Test 1: Complete Experienced Entrepreneur -> HIGH Readiness
    # -------------------------------------------------------------------------
    def test_01_complete_experienced_entrepreneur_high_readiness(self):
        payload = {
            "business_profile": {
                "business_id": "flour_milling_micro",
                "specific_business": "Atta Chakki Unit",
                "category": "Food Processing"
            },
            "user_profile": {
                "skills": {
                    "skills": ["Chakki Stone dressing", "Motor maintenance", "Grain weighment"],
                    "skill_level": "EXPERT"
                },
                "experience": {
                    "years_of_experience": 5.0,
                    "domain": "Grain Milling",
                    "prior_business_ownership": True
                },
                "training": {
                    "has_formal_training": True,
                    "certifications": ["FoSTaC Food Safety Certificate", "PMKVY Milling"]
                },
                "resources": {
                    "available_area_sqft": 300.0,
                    "power_connection_type": "THREE_PHASE_COMMERCIAL",
                    "land_or_premises_available": True
                },
                "operations": {
                    "commitment_type": "FULL_TIME",
                    "available_family_helpers": 1,
                    "hired_workers_planned": 1
                }
            }
        }
        res = entrepreneur_profile_engine.analyze(payload)

        assert res.success is True
        assert res.status == "READY"
        assert res.readiness_level == "HIGH"
        assert res.readiness_score >= 80.0
        assert res.component_scores["skills"].score >= 80.0
        assert res.component_scores["experience"].score >= 90.0
        assert res.component_scores["training"].score >= 85.0
        assert res.component_scores["resources"].score >= 85.0
        assert res.component_scores["operational_readiness"].score >= 85.0
        assert len(res.strengths) >= 3
        assert res.confidence >= 0.90
        assert res.provenance.benchmark_node_id == "flour_milling_micro"

    # -------------------------------------------------------------------------
    # Test 2: Novice Entrepreneur (Zero Experience, Minimal Skills) -> DEVELOPING
    # -------------------------------------------------------------------------
    def test_02_novice_entrepreneur_zero_experience_developing_readiness(self):
        payload = {
            "business_profile": {
                "business_id": "flour_milling_micro",
                "specific_business": "Atta Chakki Unit"
            },
            "user_profile": {
                "skills": {
                    "skills": ["General helpers"],
                    "skill_level": "NOVICE"
                },
                "experience": {
                    "years_of_experience": 0.0,
                    "prior_business_ownership": False
                },
                "training": {
                    "has_formal_training": False,
                    "willing_to_undergo_training": True
                },
                "resources": {
                    "available_area_sqft": 100.0,
                    "power_connection_type": "SINGLE_PHASE"
                },
                "operations": {
                    "commitment_type": "PART_TIME",
                    "available_family_helpers": 0
                }
            }
        }
        res = entrepreneur_profile_engine.analyze(payload)

        assert res.success is True
        assert res.status == "READY"
        assert res.readiness_level in ["DEVELOPING", "MODERATE", "LOW"]
        assert res.readiness_score < 65.0
        assert len(res.gaps) >= 2
        assert any(g.dimension == "EXPERIENCE" for g in res.gaps)
        assert len(res.required_support) >= 1

    # -------------------------------------------------------------------------
    # Test 3: Missing Critical Fields -> PROFILE_INCOMPLETE with Questions
    # -------------------------------------------------------------------------
    def test_03_missing_profile_fields_triggers_profile_incomplete(self):
        payload = {
            "business_profile": {
                "business_id": "oil_expeller_unit",
                "specific_business": "Mustard Oil Expeller"
            },
            "user_profile": {
                # Completely missing skills, experience, and resources
            }
        }
        res = entrepreneur_profile_engine.analyze(payload)

        assert res.success is True
        assert res.status == "PROFILE_INCOMPLETE"
        assert res.readiness_level == "INCOMPLETE"
        assert len(res.missing_fields) >= 2
        assert len(res.questions) >= 2
        assert any("skills" in q.field for q in res.questions)
        assert any("experience" in q.field for q in res.questions)
        # Ensure questions contain localized Hindi
        assert any(len(q.question_hi) > 0 for q in res.questions)

    # -------------------------------------------------------------------------
    # Test 4: Skill Matching Exact and Partial Domain Tokens
    # -------------------------------------------------------------------------
    def test_04_skill_matching_exact_and_partial_domain_tokens(self):
        ep = {
            "skills": {
                "skills": ["chakki taankna (stone dressing)", "motor rewinding"],
                "certified_skills": ["ITI Mechanical"]
            }
        }
        reqs = entrepreneur_profile_engine.requirements_repo.get_by_business("flour_milling_micro")
        comp = entrepreneur_profile_engine.evaluate_skills(ep, reqs, "flour_milling_micro")

        assert comp.score >= 70.0
        assert comp.status in ["STRONG", "ADEQUATE"]
        assert len(comp.matched_items) >= 1

    # -------------------------------------------------------------------------
    # Test 5: Experience Threshold Scaling
    # -------------------------------------------------------------------------
    def test_05_experience_threshold_scaling(self):
        # 1 year vs 2 year required benchmark
        ep_1yr = {"experience": {"years_of_experience": 1.0}}
        comp_1yr = entrepreneur_profile_engine.evaluate_experience(ep_1yr, "flour_milling_micro")
        assert comp_1yr.score == 57.5
        assert comp_1yr.status == "ADEQUATE"

        # 4 years vs 2 year required benchmark
        ep_4yr = {"experience": {"years_of_experience": 4.0}}
        comp_4yr = entrepreneur_profile_engine.evaluate_experience(ep_4yr, "flour_milling_micro")
        assert comp_4yr.score >= 90.0
        assert comp_4yr.status == "STRONG"

    # -------------------------------------------------------------------------
    # Test 6: Mandatory Training / FoSTaC Checking
    # -------------------------------------------------------------------------
    def test_06_mandatory_training_certifications_fostac_check(self):
        ep_certified = {
            "training": {
                "has_formal_training": True,
                "certifications": ["FoSTaC Food Safety Certificate"]
            }
        }
        comp = entrepreneur_profile_engine.evaluate_training(ep_certified, None, "spice_grinding_packaging")
        assert comp.score >= 85.0
        assert comp.status == "STRONG"
        assert len(comp.missing_items) == 0

    # -------------------------------------------------------------------------
    # Test 7: Power & Infrastructure Adequacy
    # -------------------------------------------------------------------------
    def test_07_power_and_infrastructure_adequacy(self):
        # 3-Phase power required for chakki
        ep_3phase = {
            "resources": {
                "available_area_sqft": 250.0,
                "power_connection_type": "THREE_PHASE_COMMERCIAL"
            }
        }
        reqs = entrepreneur_profile_engine.requirements_repo.get_by_business("flour_milling_micro")
        comp = entrepreneur_profile_engine.evaluate_resources(ep_3phase, reqs, "flour_milling_micro")
        assert comp.score >= 85.0

        # Single phase power -> lower score and shortfall in missing_items
        ep_1phase = {
            "resources": {
                "available_area_sqft": 250.0,
                "power_connection_type": "SINGLE_PHASE"
            }
        }
        comp_1phase = entrepreneur_profile_engine.evaluate_resources(ep_1phase, reqs, "flour_milling_micro")
        assert comp_1phase.score < comp.score
        assert any("power" in m.lower() for m in comp_1phase.missing_items)

    # -------------------------------------------------------------------------
    # Test 8: Operational Readiness Commitment & Workforce
    # -------------------------------------------------------------------------
    def test_08_operational_readiness_commitment_and_workforce(self):
        ep_full = {
            "operations": {
                "commitment_type": "FULL_TIME",
                "available_family_helpers": 1,
                "hired_workers_planned": 1
            }
        }
        reqs = entrepreneur_profile_engine.requirements_repo.get_by_business("flour_milling_micro")
        comp = entrepreneur_profile_engine.evaluate_operations(ep_full, reqs, "flour_milling_micro")
        assert comp.score >= 90.0
        assert comp.status == "STRONG"

    # -------------------------------------------------------------------------
    # Test 9: Multilingual Clarification Extraction (Hindi Text)
    # -------------------------------------------------------------------------
    def test_09_multilingual_clarification_extraction_hindi(self):
        hindi_text = "मैंने पांच साल कपड़ों की दुकान में काम किया है और 3 phase बिजली है।"
        facts = clarification_extractor.extract_from_text(hindi_text)

        assert "experience" in facts
        assert facts["experience"]["years_of_experience"] == 5.0
        assert "resources" in facts
        assert facts["resources"]["power_connection_type"] == "THREE_PHASE_COMMERCIAL"

    # -------------------------------------------------------------------------
    # Test 10: Deterministic Provenance and Audit Trail
    # -------------------------------------------------------------------------
    def test_10_deterministic_provenance_and_audit_trail(self):
        payload = {
            "business_profile": {"business_id": "solar_pump_repair_service"},
            "user_profile": {"experience": {"years_of_experience": 3.0}}
        }
        res = entrepreneur_profile_engine.analyze(payload)
        assert res.provenance.engine == "STAGE_10_ENTREPRENEUR_PROFILE_ENGINE"
        assert res.provenance.evaluation_type == "DETERMINISTIC_RULES"
        assert res.provenance.benchmark_node_id == "solar_pump_repair_service"

    # -------------------------------------------------------------------------
    # Test 11: REST API POST /api/v1/entrepreneur-profile/analyze
    # -------------------------------------------------------------------------
    def test_11_api_analyze_endpoint(self, client):
        payload = {
            "business_profile": {
                "business_id": "flour_milling_micro",
                "specific_business": "Atta Chakki Unit"
            },
            "user_profile": {
                "skills": {"skills": ["Chakki operations"]},
                "experience": {"years_of_experience": 3.0},
                "training": {"has_formal_training": True},
                "resources": {"available_area_sqft": 200.0, "power_connection_type": "THREE_PHASE_COMMERCIAL"},
                "operations": {"commitment_type": "FULL_TIME"}
            }
        }
        response = client.post("/api/v1/entrepreneur-profile/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "READY"
        assert data["readiness_score"] >= 70.0

    # -------------------------------------------------------------------------
    # Test 12: REST API POST /api/v1/entrepreneur-profile/clarify
    # -------------------------------------------------------------------------
    def test_12_api_clarify_endpoint(self, client):
        payload = {
            "text": "मेरे पास 300 sq ft जगह है और 3 साल का अनुभव है",
            "field": "resources.available_area_sqft"
        }
        response = client.post("/api/v1/entrepreneur-profile/clarify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "experience" in data["extracted_facts"] or "resources" in data["extracted_facts"]

    # -------------------------------------------------------------------------
    # Test 13: REST API GET /api/v1/entrepreneur-profile/health
    # -------------------------------------------------------------------------
    def test_13_api_health_endpoint(self, client):
        response = client.get("/api/v1/entrepreneur-profile/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["stage"] == 10
        assert data["evaluation_mode"] == "DETERMINISTIC_RULES"
