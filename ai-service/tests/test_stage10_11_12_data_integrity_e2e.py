"""
End-to-End Integration and Unit Tests for:
- Stage 10: Entrepreneur Profile Clarification Extraction & Deterministic Benchmark Scoring
- Stage 11: Multi-Vector Risk Engine Data Integrity & DATA_GAP Handling
- Stage 12: Feasibility Engine 4-Pillar Mathematical Synthesis & Validation Gating
"""
import pytest
from app.services.entrepreneur_profile_engine.clarification_extractor import ClarificationExtractor
from app.services.entrepreneur_profile_engine.engine import EntrepreneurProfileEngine
from app.services.risk_engine.engine import RiskEngine
from app.services.feasibility_engine.feature_vector import FeasibilityFeatureVectorBuilder
from app.services.feasibility_engine.synthesis_engine import FeasibilitySynthesisEngine
from app.services.feasibility_engine.critical_gates import CriticalGatesEvaluator
from app.schemas.feasibility import FeasibilityEvaluationRequest


def test_stage10_multilingual_clarification_extraction():
    """Test 1: Clarification extractor handles English and Hindi numeric phrases correctly."""
    extractor = ClarificationExtractor()

    # English: "I worked one year in a saree shop as a staff"
    res_en = extractor.extract_from_text(
        text="I worked one year in a saree shop as a staff",
        target_field="experience.years_of_experience",
        business_context={"business_id": "saree_retail"}
    )
    assert "experience" in res_en
    assert res_en["experience"]["years_of_experience"] == 1.0
    assert res_en["experience"]["source"] == "USER_CLARIFICATION"
    assert res_en["experience"]["raw_text"] == "I worked one year in a saree shop as a staff"

    # Hindi: "मैंने एक साल साड़ी की दुकान में काम किया है"
    res_hi = extractor.extract_from_text(
        text="मैंने एक साल साड़ी की दुकान में काम किया है",
        target_field="experience.years_of_experience",
        business_context={"business_id": "saree_retail"}
    )
    assert "experience" in res_hi
    assert res_hi["experience"]["years_of_experience"] == 1.0
    assert res_hi["experience"]["source"] == "USER_CLARIFICATION"


def test_stage10_benchmark_score_award_100():
    """Test 2: When user experience matches or exceeds domain benchmark, award 100/100."""
    ep_engine = EntrepreneurProfileEngine()

    profile_payload = {
        "business_profile": {
            "business_id": "saree_retail",
            "specific_business": "Saree Retail"
        },
        "entrepreneur_profile": {
            "experience": {
                "years_of_experience": 1.0,
                "relevant_industry_experience": True,
                "source": "USER_CLARIFICATION"
            },
            "skills": {
                "has_core_domain_skills": True,
                "skills_list": ["sales", "customer_handling"]
            },
            "training": {
                "has_formal_training": True
            },
            "resources": {
                "has_commercial_space": True,
                "commercial_space_sqft": 200,
                "power_connection": "SINGLE_PHASE_COMMERCIAL"
            }
        }
    }

    evaluated = ep_engine.analyze(profile_payload)

    exp_comp = evaluated.component_scores["experience"] if isinstance(evaluated.component_scores, dict) else getattr(evaluated.component_scores, "experience")
    exp_score = exp_comp["score"] if isinstance(exp_comp, dict) else getattr(exp_comp, "score")
    assert exp_score == 100.0, f"Expected 100.0 on meeting benchmark, got {exp_score}"
    
    exp_status = exp_comp["status"] if isinstance(exp_comp, dict) else getattr(exp_comp, "status")
    assert exp_status == "STRONG"
    
    exp_calc = exp_comp["calculation"] if isinstance(exp_comp, dict) else getattr(exp_comp, "calculation")
    assert "100/100" in exp_calc


def test_stage11_risk_engine_consumes_upstream_and_flags_data_gap():
    """Test 3: Risk engine evaluates real upstream evidence and flags DATA_GAP without fake zeroes."""
    risk_engine = RiskEngine()

    # Case A: Complete payload
    complete_payload = {
        "business_profile": {"business_id": "saree_retail", "specific_business": "Saree Retail"},
        "stage9_financial_analysis": {
            "debt_service": {"dscr": 1.85},
            "break_even": {"break_even_point_percentage": 48.0}
        },
        "stage8_opportunity_evaluation": {
            "opportunity_result": {
                "market_opportunity_score": 0.88,
                "competition_opportunity": 0.80
            }
        },
        "stage10_entrepreneur_profile": {
            "readiness_score": 85.0,
            "status": "READY",
            "gaps": []
        }
    }
    res_complete = risk_engine.analyze(complete_payload)
    assert res_complete.overall_risk_score is not None
    assert res_complete.category_risks["FINANCIAL"].level == "LOW"
    assert res_complete.category_risks["FINANCIAL"].score == 0.18
    assert res_complete.category_risks["MARKET"].level == "LOW"

    # Case B: Completely missing payload
    empty_payload = {
        "business_profile": {"business_id": "unknown_business"}
    }
    res_empty = risk_engine.analyze(empty_payload)
    assert res_empty.category_risks["FINANCIAL"].level == "DATA_GAP"
    assert res_empty.category_risks["FINANCIAL"].score is None


def test_stage12_feasibility_exact_4_pillar_math():
    """Test 4: Stage 12 calculates exact weighted 4-pillar math (Market 25%, Finance 35%, Ent 20%, Risk 20%)."""
    vector_builder = FeasibilityFeatureVectorBuilder()
    synthesis_engine = FeasibilitySynthesisEngine()
    gates_evaluator = CriticalGatesEvaluator()

    # Inputs: Market=88.0, Finance=82.0 (via DSCR 1.60), Entrepreneur=78.0, Risk=0.32 (Resilience=68.0)
    opp_data = {
        "opportunity_result": {
            "market_opportunity_score": 0.88,
            "demand_score": 0.85,
            "competition_opportunity": 0.70
        }
    }
    fin_data = {
        "financial_analysis": {
            "dscr": 1.60,  # maps to 82.0
            "break_even_point_percentage": 55.0,
            "total_project_cost": 500000.0,
            "estimated_financeable_loan": 375000.0
        }
    }
    ent_data = {
        "entrepreneur_profile": {
            "readiness_score": 78.0,
            "component_scores": {
                "skills": {"score": 80.0},
                "experience": {"score": 100.0},
                "training": {"score": 70.0},
                "resources": {"score": 75.0}
            }
        }
    }
    rsk_data = {
        "risk_analysis": {
            "overall_risk_score": 0.32,
            "overall_risk_severity": "LOW",
            "category_risks": {
                "FINANCIAL": {"score": 0.20, "level": "LOW"},
                "MARKET": {"score": 0.25, "level": "LOW"},
                "OPERATIONAL": {"score": 0.20, "level": "LOW"},
                "INFRASTRUCTURE": {"score": 0.16, "level": "LOW"}
            }
        }
    }

    feature_vec = vector_builder.build_feature_vector(
        opportunity_data=opp_data,
        financial_data=fin_data,
        entrepreneur_data=ent_data,
        risk_data=rsk_data
    )

    assert feature_vec.market_opportunity_score.value == 88.0
    assert feature_vec.market_opportunity_score.status == "VERIFIED"
    assert feature_vec.financial_viability_score.value == 82.0
    assert feature_vec.entrepreneur_readiness_score.value == 78.0
    assert feature_vec.overall_risk_score.value == 0.32

    gates = gates_evaluator.evaluate_gates(
        feature_vector=feature_vec,
        business_profile={"specific_business": "Saree Retail"}
    )

    (
        composite_score,
        decision,
        recommendation,
        confidence,
        pillar_scores,
        positive_drivers,
        key_constraints,
        conditions,
        provenance,
        data_completeness
    ) = synthesis_engine.synthesize(
        feature_vector=feature_vec,
        critical_gates=gates,
        business_title="Saree Retail"
    )

    # Expected calculation:
    # Market: 88.0 * 0.25 = 22.0
    # Finance: 82.0 * 0.35 = 28.7
    # Entrepreneur: 78.0 * 0.20 = 15.6
    # Risk Resilience: (1.0 - 0.32)*100 = 68.0 -> 68.0 * 0.20 = 13.6
    # Total = 22.0 + 28.7 + 15.6 + 13.6 = 79.9
    assert composite_score == 79.9
    assert recommendation == "YES"
    assert decision == "VIABLE"
    assert data_completeness["complete"] is True
    assert data_completeness["is_authoritative"] is True


def test_stage12_missing_upstream_data_blocks_yes():
    """Test 5: When upstream data has DATA_GAP, Feasibility recommendation must be NEEDS_VALIDATION, not YES."""
    vector_builder = FeasibilityFeatureVectorBuilder()
    synthesis_engine = FeasibilitySynthesisEngine()
    gates_evaluator = CriticalGatesEvaluator()

    # Only finance is provided; market, entrepreneur, risk are missing
    fin_data = {
        "financial_analysis": {
            "dscr": 1.70,
            "break_even_point_percentage": 50.0
        }
    }

    feature_vec = vector_builder.build_feature_vector(
        financial_data=fin_data
    )

    assert feature_vec.market_opportunity_score.status == "DATA_GAP"
    assert feature_vec.market_opportunity_score.value is None

    gates = gates_evaluator.evaluate_gates(
        feature_vector=feature_vec,
        business_profile={"specific_business": "Saree Retail"}
    )

    (
        composite_score,
        decision,
        recommendation,
        confidence,
        pillar_scores,
        _, _, _, _,
        data_completeness
    ) = synthesis_engine.synthesize(
        feature_vector=feature_vec,
        critical_gates=gates,
        business_title="Saree Retail"
    )

    assert decision == "DATA_INSUFFICIENT"
    assert recommendation == "NEEDS_VALIDATION"
    assert data_completeness["complete"] is False
    assert data_completeness["is_authoritative"] is False
