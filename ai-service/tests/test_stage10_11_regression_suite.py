"""
Fast Deterministic Regression Suite for Stage 10 (Entrepreneur Profile) and Stage 11 (Risk Engine).
Validates requirements A through M and Section 18 Regression Scenario:
A. Voice clarification contract & transcribe endpoint
B. Hindi clarification extraction
C. English clarification extraction
D. Hinglish extraction
E. Profile merge and persistence
F. Missing field disappears after answer
G. Stage 10 score changes after valid clarification
H. Stage 11 risk changes according to Stage 10 updates
I. Business-context differentiation (Saree Retail vs Dairy vs Rice Mill vs Kirana vs Tailoring)
J. Missing benchmark -> UNKNOWN, not fabricated
K. Critical risk ceiling enforcement
L. Orchestrator workflow pause on incomplete profile
M. Orchestrator workflow continues only after Stage 10 completion
Section 18. Exact Saree Retail Regression Scenario
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.entrepreneur_profile_engine import (
    entrepreneur_profile_engine,
    clarification_extractor,
)
from app.services.risk_engine import risk_engine
from app.services.financial_engine import financial_engine
from app.services.opportunity_evaluation_engine import opportunity_evaluation_engine
from app.services.market_intelligence_engine import market_intelligence_engine
from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
    ClarificationQuestion,
)
from app.schemas.risk_analysis import RiskAnalysisRequest, RiskAnalysisResponse


@pytest.fixture
def client():
    return TestClient(app)


class TestStage10Stage11RegressionSuite:
    """
    Focused, fast, deterministic verification suite (< 5 seconds total runtime).
    """

    # -------------------------------------------------------------------------
    # A. Voice Clarification Contract & Dedicated Transcribe Flow
    # -------------------------------------------------------------------------
    def test_A_voice_transcribe_and_clarification_contract(self, client):
        from unittest.mock import AsyncMock
        with patch("app.api.routes.intake.sarvam_stt_service.transcribe_audio", new_callable=AsyncMock) as mock_stt:
            mock_stt.return_value = ("मेरे पास पांच साल का अनुभव है और दुकान भी है", "hi-IN")
            dummy_wav = io.BytesIO(b"RIFF" + b"\x00" * 256)
            response = client.post(
                "/api/v1/intake/transcribe",
                files={"file": ("clarify.wav", dummy_wav, "audio/wav")},
                data={"language_code": "hi-IN"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "पांच साल" in data["transcript"]

        # 2. Call clarify with transcript
        clarify_payload = {
            "text": data["transcript"],
            "field": "experience.years_of_experience",
            "business_context": {"specific_business": "Saree Retail", "category": "Retail"}
        }
        res_clarify = client.post("/api/v1/entrepreneur-profile/clarify", json=clarify_payload)
        assert res_clarify.status_code == 200
        clarify_data = res_clarify.json()
        assert clarify_data["success"] is True
        assert clarify_data["extracted_facts"]["experience"]["years_of_experience"] == 5.0

    # -------------------------------------------------------------------------
    # B. Hindi Clarification Extraction
    # -------------------------------------------------------------------------
    def test_B_hindi_clarification_extraction(self):
        hindi_text = "मैं पिछले पांच साल से साड़ी बेच रहा हूं और ग्राहकों से बिक्री का अनुभव है।"
        facts = clarification_extractor.extract_from_text(
            text=hindi_text,
            target_field="experience.years_of_experience",
            business_context={"specific_business": "Saree Retail"}
        )
        assert "experience" in facts
        assert facts["experience"]["years_of_experience"] == 5.0
        assert facts["experience"]["domain"] == "saree_retail"
        assert "skills" in facts
        assert any("sales" in s or "retail" in s or "saree" in s for s in facts["skills"]["skills"])

    # -------------------------------------------------------------------------
    # C. English Clarification Extraction
    # -------------------------------------------------------------------------
    def test_C_english_clarification_extraction(self):
        eng_text = "I have 4 years of hands-on experience in saree retail and customer management with a 300 sq ft shop."
        facts = clarification_extractor.extract_from_text(
            text=eng_text,
            target_field="experience.years_of_experience",
            business_context={"specific_business": "Saree Retail"}
        )
        assert facts["experience"]["years_of_experience"] == 4.0
        assert facts["resources"]["available_area_sqft"] == 300.0
        assert facts["resources"]["land_or_premises_available"] is True

    # -------------------------------------------------------------------------
    # D. Hinglish Extraction
    # -------------------------------------------------------------------------
    def test_D_hinglish_extraction(self):
        hinglish_text = "Mera 3 saal ka experience hai tailoring and garment stitching mein aur 3-phase electricity available hai"
        facts = clarification_extractor.extract_from_text(
            text=hinglish_text,
            target_field="skills",
            business_context={"specific_business": "Tailoring Shop"}
        )
        assert facts["experience"]["years_of_experience"] == 3.0
        assert facts["resources"]["power_connection_type"] == "THREE_PHASE_COMMERCIAL"
        assert len(facts["skills"]["skills"]) >= 1

    # -------------------------------------------------------------------------
    # E. Profile Merge & Persistence (Non-destructive update)
    # -------------------------------------------------------------------------
    def test_E_profile_merge_persistence(self):
        existing_profile = {
            "skills": {"skills": ["Customer greeting"], "source": "USER_INPUT"},
            "resources": {"available_area_sqft": 200.0, "source": "USER_INPUT"}
        }
        updates = {
            "skills": {"skills": ["Saree draping", "Inventory bookkeeping"]},
            "experience": {"years_of_experience": 5.0, "domain": "saree_retail"}
        }
        merged = entrepreneur_profile_engine.merge_profiles(existing_profile, updates)

        # Existing resources must NOT be overwritten
        assert merged["resources"]["available_area_sqft"] == 200.0
        # Skills must be merged cumulatively
        assert "Customer greeting" in merged["skills"]["skills"]
        assert "Saree draping" in merged["skills"]["skills"]
        # Experience must be set
        assert merged["experience"]["years_of_experience"] == 5.0

    # -------------------------------------------------------------------------
    # F. Missing Field Disappears After Clarification
    # -------------------------------------------------------------------------
    def test_F_missing_field_disappears_after_answer(self):
        initial_payload = {
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "user_profile": {}  # Completely missing
        }
        res1 = entrepreneur_profile_engine.analyze(initial_payload)
        assert "skills" in res1.missing_fields
        assert "experience.years_of_experience" in res1.missing_fields
        assert len(res1.questions) >= 2

        # Provide skills and experience
        answered_payload = {
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "user_profile": {
                "skills": {"skills": ["Saree sales", "Inventory accounting"]},
                "experience": {"years_of_experience": 4.0, "domain": "saree_retail"},
                "resources": {"available_area_sqft": 200.0},
                "operations": {"commitment_type": "FULL_TIME"}
            }
        }
        res2 = entrepreneur_profile_engine.analyze(answered_payload)
        assert "skills" not in res2.missing_fields
        assert "experience.years_of_experience" not in res2.missing_fields
        assert res2.status == "READY"
        assert len(res2.questions) == 0

    # -------------------------------------------------------------------------
    # G. Stage 10 Score Changes After Valid Clarification
    # -------------------------------------------------------------------------
    def test_G_stage10_score_changes_after_valid_clarification(self):
        incomplete_payload = {
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "user_profile": {}
        }
        res_before = entrepreneur_profile_engine.analyze(incomplete_payload)
        assert res_before.status == "PROFILE_INCOMPLETE"
        initial_score = res_before.readiness_score

        clarified_payload = {
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "user_profile": {
                "skills": {"skills": ["Saree matching", "Counter sales", "Khata bookkeeping"], "skill_level": "EXPERT"},
                "experience": {"years_of_experience": 5.0, "prior_business_ownership": True},
                "training": {"has_formal_training": True},
                "resources": {"available_area_sqft": 250.0, "land_or_premises_available": True},
                "operations": {"commitment_type": "FULL_TIME", "available_family_helpers": 1}
            }
        }
        res_after = entrepreneur_profile_engine.analyze(clarified_payload)
        assert res_after.status == "READY"
        assert res_after.readiness_score > initial_score
        assert res_after.readiness_score >= 80.0

    # -------------------------------------------------------------------------
    # H. Stage 11 Risk Changes According to Stage 10 Readiness Update
    # -------------------------------------------------------------------------
    def test_H_stage11_risk_changes_according_to_stage10(self):
        biz = {"business_id": "saree_retail", "specific_business": "Saree Retail"}

        # Case 1: Incomplete / Weak Stage 10
        stage11_input_weak = {
            "business_profile": biz,
            "entrepreneur_readiness": {
                "status": "PROFILE_INCOMPLETE",
                "readiness_score": 30.0,
                "gaps": [{"dimension": "SKILLS", "gap_description": "No prior retail experience"}]
            }
        }
        res_weak = risk_engine.analyze(stage11_input_weak)
        assert res_weak.category_risks["OPERATIONAL"].severity == "HIGH"
        assert res_weak.category_risks["OPERATIONAL"].score >= 0.70

        # Case 2: Strong / Clarified Stage 10
        stage11_input_strong = {
            "business_profile": biz,
            "entrepreneur_readiness": {
                "status": "READY",
                "readiness_score": 85.0,
                "gaps": []
            }
        }
        res_strong = risk_engine.analyze(stage11_input_strong)
        assert res_strong.category_risks["OPERATIONAL"].severity == "LOW"
        assert res_strong.category_risks["OPERATIONAL"].score <= 0.30

    # -------------------------------------------------------------------------
    # I. Business-Context Differentiation (5 Priority Categories)
    # -------------------------------------------------------------------------
    def test_I_business_context_differentiation(self):
        # 1. Saree Retail: Non-perishable, low power, seasonal wedding demand
        res_saree = risk_engine.analyze({"business_profile": {"business_id": "saree_retail"}})
        assert res_saree.category_risks["SUPPLY_CHAIN"].severity == "LOW"
        assert res_saree.category_risks["INFRASTRUCTURE"].severity == "LOW"

        # 2. Dairy Micro-Chilling: Perishable, high cold chain risk
        res_dairy = risk_engine.analyze({"business_profile": {"business_id": "dairy_micro_chilling_aggregator"}})
        assert res_dairy.category_risks["SUPPLY_CHAIN"].severity == "HIGH"
        assert any("perishable" in d.lower() or "cold chain" in d.lower() for d in res_dairy.category_risks["SUPPLY_CHAIN"].drivers)

        # 3. Rice Mill: Heavy 3-phase power requirement, post-harvest crop seasonality
        res_rice = risk_engine.analyze({"business_profile": {"business_id": "rice_mill"}})
        assert res_rice.category_risks["SEASONAL"].severity == "MEDIUM"

        # 4. Grocery / Kirana: Daily non-seasonal consumption, low supply risk
        res_kirana = risk_engine.analyze({"business_profile": {"business_id": "grocery_store"}})
        assert res_kirana.category_risks["SEASONAL"].score <= 0.25
        assert res_kirana.category_risks["SUPPLY_CHAIN"].severity == "LOW"

        # 5. Tailoring: Service-oriented, minimal supply risk
        res_tailor = risk_engine.analyze({"business_profile": {"business_id": "tailoring_shop"}})
        assert res_tailor.category_risks["SUPPLY_CHAIN"].score <= 0.25

    # -------------------------------------------------------------------------
    # J. Missing Benchmark -> UNKNOWN, Not Fabricated
    # -------------------------------------------------------------------------
    def test_J_missing_benchmark_defaults_to_unknown(self):
        payload = {
            "business_profile": {"business_id": "completely_unknown_quantum_enterprise"}
        }
        res = risk_engine.analyze(payload)
        assert res.category_risks["FINANCIAL"].severity == "UNKNOWN"
        assert res.category_risks["MARKET"].severity == "UNKNOWN"
        assert "BENCHMARK_DATA_UNAVAILABLE" in res.category_risks["FINANCIAL"].source_stage

    # -------------------------------------------------------------------------
    # K. Critical Risk Ceiling Rule
    # -------------------------------------------------------------------------
    def test_K_critical_risk_ceiling(self):
        # A single catastrophic driver (e.g. DSCR = 0.90) forces overall risk to CRITICAL/HIGH
        payload = {
            "business_profile": {"business_id": "saree_retail"},
            "financial_analysis": {
                "financial_viability": {"debt_service_coverage_ratio": 0.90}
            },
            "entrepreneur_readiness": {"readiness_score": 95.0}  # Perfect entrepreneur
        }
        res = risk_engine.analyze(payload)
        assert res.overall_risk_severity in ["HIGH", "CRITICAL"]
        assert res.critical_risks_count >= 1
        assert res.provenance.critical_ceiling_applied is True

    # -------------------------------------------------------------------------
    # L & M. Workflow Ordering: Pause on Incomplete Profile -> Resume on Completion
    # -------------------------------------------------------------------------
    def test_L_and_M_orchestrator_pause_and_continue_flow(self):
        # Initial: Incomplete entrepreneur profile
        biz_context = {"business_id": "saree_retail", "specific_business": "Saree Retail"}
        ep_incomplete = {}

        stage10_res_init = entrepreneur_profile_engine.analyze({
            "business_profile": biz_context,
            "entrepreneur_profile": ep_incomplete
        })
        assert stage10_res_init.status == "PROFILE_INCOMPLETE"

        # Simulate user providing clarification
        answer_text = "5 years retail saree sales experience with 200 sqft shop"
        facts = clarification_extractor.extract_from_text(answer_text, business_context=biz_context)
        ep_updated = entrepreneur_profile_engine.merge_profiles(ep_incomplete, facts)
        ep_updated["operations"] = {"commitment_type": "FULL_TIME"}

        stage10_res_final = entrepreneur_profile_engine.analyze({
            "business_profile": biz_context,
            "entrepreneur_profile": ep_updated
        })
        assert stage10_res_final.status == "READY"
        assert stage10_res_final.readiness_score >= 70.0

        # Now Stage 11 executes against completed Stage 10
        stage11_res = risk_engine.analyze({
            "business_profile": biz_context,
            "entrepreneur_readiness": stage10_res_final.model_dump()
        })
        assert stage11_res.success is True
        assert stage11_res.category_risks["OPERATIONAL"].severity == "LOW"

    # -------------------------------------------------------------------------
    # Section 18. Exact Saree Retail Regression Scenario
    # -------------------------------------------------------------------------
    def test_section_18_exact_saree_retail_regression_scenario(self, client):
        """
        Initial:
        Business = Saree Retail
        Capital = ₹1,00,000
        Skills = missing
        Experience = missing

        Stage 10: PROFILE_INCOMPLETE

        User voice/text:
        "मैं पिछले पांच साल से साड़ी बेच रहा हूं और ग्राहकों से बिक्री का अनुभव है।"

        Expected:
        skills updated
        experience_years = 5
        experience_domain = saree_retail
        missing_fields reduced
        readiness recalculated
        questions disappear
        Stage 11 consumes UPDATED Stage 10 result.
        """
        # 1. Stage 10 Initial Evaluation with 3 missing fields
        initial_payload = {
            "analysis_id": "regression-saree-101",
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Saree Retail",
                "category": "Retail"
            },
            "user_profile": {}  # Missing skills, experience, and resources
        }
        res_init = entrepreneur_profile_engine.analyze(initial_payload)
        assert res_init.status == "PROFILE_INCOMPLETE"
        assert "skills" in res_init.missing_fields
        assert "experience.years_of_experience" in res_init.missing_fields
        assert "resources.available_area_sqft" in res_init.missing_fields
        assert len(res_init.questions) >= 3

        # 2. User answers Q1 (Experience & Skills) via Hindi Voice / Text Clarification
        clarify_req1 = {
            "analysis_id": "regression-saree-101",
            "text": "मैं पिछले पांच साल से साड़ी बेच रहा हूं और ग्राहकों से बिक्री का अनुभव है।",
            "field": "experience.years_of_experience",
            "language": "hi",
            "business_context": {
                "business_id": "saree_retail",
                "specific_business": "Saree Retail"
            }
        }
        clarify_resp1 = client.post("/api/v1/entrepreneur-profile/clarify", json=clarify_req1)
        assert clarify_resp1.status_code == 200
        data1 = clarify_resp1.json()

        assert data1["success"] is True
        assert data1["extracted_facts"]["experience"]["years_of_experience"] == 5.0
        assert data1["extracted_facts"]["experience"]["domain"] == "saree_retail"
        assert len(data1["extracted_facts"]["skills"]["skills"]) >= 1

        # 3. Verify Stage 10 retained the remaining resources question and status is still incomplete
        readiness1 = data1["readiness_evaluation"]
        assert readiness1 is not None
        assert "experience.years_of_experience" not in readiness1["missing_fields"]
        assert "skills" not in readiness1["missing_fields"]
        assert "resources.available_area_sqft" in readiness1["missing_fields"]
        assert readiness1["status"] == "PROFILE_INCOMPLETE"

        # 4. User answers remaining resources question
        clarify_req2 = {
            "analysis_id": "regression-saree-101",
            "text": "मेरे पास 300 स्क्वायर फीट की पक्की दुकान है।",
            "field": "resources.available_area_sqft",
            "language": "hi",
            "business_context": {
                "business_id": "saree_retail",
                "specific_business": "Saree Retail"
            }
        }
        clarify_resp2 = client.post("/api/v1/entrepreneur-profile/clarify", json=clarify_req2)
        assert clarify_resp2.status_code == 200
        data2 = clarify_resp2.json()
        readiness2 = data2["readiness_evaluation"]
        assert readiness2 is not None
        assert len(readiness2["missing_fields"]) == 0
        assert readiness2["status"] == "READY"
        assert readiness2["readiness_score"] >= 70.0

        # 5. Stage 11 consumes updated Stage 10
        stage11_payload = {
            "analysis_id": "regression-saree-101",
            "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
            "entrepreneur_readiness": readiness2
        }
        stage11_res = risk_engine.analyze(stage11_payload)
        assert stage11_res.success is True
        assert stage11_res.category_risks["OPERATIONAL"].severity == "LOW"
        assert stage11_res.category_risks["SUPPLY_CHAIN"].severity == "LOW"

        # 6. Switching business to Dairy shifts risk profile accordingly
        dairy_payload = {
            "analysis_id": "regression-dairy-102",
            "business_profile": {"business_id": "dairy_micro_chilling_aggregator", "specific_business": "Dairy Micro-Chilling"},
            "entrepreneur_readiness": readiness2
        }
        dairy_res = risk_engine.analyze(dairy_payload)
        assert dairy_res.category_risks["SUPPLY_CHAIN"].severity == "HIGH"
        assert any("perishable" in d.lower() or "cold chain" in d.lower() for d in dairy_res.category_risks["SUPPLY_CHAIN"].drivers)
