"""
Unit and Integration Tests for KALPA Stage 14.1 Intelligent Gap Resolution & Sarvam Question Framing.

Verifies:
1. Canonical Field Registry & Alias Resolution (resolve_canonical_id, aliases, etc.)
2. Non-askable field filtering (calculated, derived, engine outputs are never askable)
3. Deterministic question prioritization (Blocking CRITICAL > Blocking HIGH > Blocking MEDIUM > Non-blocking)
4. Sarvam multilingual framing & fallback behavior for English, Hindi, and Marathi
5. Question structure adherence (question, helper_text, example, why_we_are_asking)
6. Resolution trace generation.
"""
import pytest
import asyncio
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    CANONICAL_FIELDS,
    FieldResolutionStatus,
    CanonicalFieldEntry,
    resolve_canonical_id,
    get_canonical_id,
    get_canonical_entry,
    is_question_allowed,
    NEVER_ASKABLE_FIELD_IDS,
    build_resolution_trace,
)
from app.services.dpr_stage1.dpr_question_framer import (
    dpr_question_framer,
    get_fallback_question,
    FramedQuestionPayload,
    CURATED_FALLBACK_CATALOG,
)
from app.services.dpr_stage1.dpr_question_engine import (
    dpr_question_engine,
    DPRQuestion,
)
from app.services.dpr_stage1.dpr_gap_analyzer import (
    DPRGapAnalysisResult,
    GapItem,
)


def test_canonical_id_resolution_and_aliases():
    """Verify that semantic aliases resolve to their canonical IDs."""
    assert resolve_canonical_id("trade_name") == "business_name"
    assert resolve_canonical_id("firm_name") == "business_name"
    assert resolve_canonical_id("enterprise_name") == "business_name"
    assert resolve_canonical_id("target_district") == "location_district"
    assert resolve_canonical_id("state") == "location_state"
    assert resolve_canonical_id("prior_experience_years") == "promoter_experience_years"
    assert resolve_canonical_id("educational_qualification") == "promoter_education"
    assert resolve_canonical_id("land_type") == "premises_status"
    assert resolve_canonical_id("plant_machinery_cost") == "cost_plant_machinery"
    assert resolve_canonical_id("own_investment") == "promoter_contribution"
    assert resolve_canonical_id("margin_money") == "promoter_contribution"
    assert resolve_canonical_id("equity_amount") == "promoter_equity_amount"


def test_non_askable_fields_enforcement():
    """Verify that calculated, derived, and engine output fields are NEVER allowed as user questions."""
    # Calculated / Financial fields must NOT be askable
    assert not is_question_allowed("total_project_cost")
    assert not is_question_allowed("promoter_equity_amount")
    assert not is_question_allowed("bank_term_loan_amount")
    assert not is_question_allowed("glance_average_dscr")
    assert not is_question_allowed("glance_break_even_utilization")
    assert not is_question_allowed("projected_pnl_statements")
    assert not is_question_allowed("loan_amortization_schedule")
    assert not is_question_allowed("scheme_subsidy_percentage")
    assert not is_question_allowed("risk_mitigation_matrix")
    assert not is_question_allowed("dynamic_swot_matrix")
    assert not is_question_allowed("means_of_finance_reconciliation")

    # True input fields MUST be allowed
    assert is_question_allowed("business_name")
    assert is_question_allowed("business_activity")
    assert is_question_allowed("premises_status")
    assert is_question_allowed("promoter_education")
    assert is_question_allowed("promoter_experience_years")


def test_resolution_trace_generation():
    """Verify diagnostic resolution trace correctly identifies resolved vs unresolved fields."""
    dpr_context_fields = {
        "business_name": {
            "status": "RESOLVED_USER",
            "source_id": "STAGE_1_INTAKE",
            "value": "Kashi Handloom Sarees"
        },
        "total_project_cost": {
            "status": "RESOLVED_ENGINE",
            "source_id": "STAGE_9_FINANCIAL_ENGINE",
            "value": 1500000.0
        },
        "premises_status": {
            "status": "USER_REQUIRED",
            "source_id": "INTAKE_GAP",
            "value": None
        }
    }

    trace_biz = build_resolution_trace("business_name", dpr_context_fields)
    assert not trace_biz.question_allowed
    assert trace_biz.value_present

    trace_cost = build_resolution_trace("total_project_cost", dpr_context_fields)
    assert not trace_cost.question_allowed

    trace_prem = build_resolution_trace("premises_status", dpr_context_fields)
    assert trace_prem.question_allowed
    assert trace_prem.status == FieldResolutionStatus.USER_REQUIRED.value


def test_curated_fallback_multilingual_catalog():
    """Verify curated fallback questions in English, Hindi, and Marathi."""
    # English
    en_q = get_fallback_question("business_name", "Business Name", "string", "Identify enterprise", "Bank requirement", None, "en")
    assert "official or proposed name" in en_q.question
    assert len(en_q.helper_text) > 0
    assert len(en_q.why_we_are_asking) > 0

    # Hindi
    hi_q = get_fallback_question("business_name", "Business Name", "string", "Identify enterprise", "Bank requirement", None, "hi")
    assert "व्यवसाय या उद्यम का क्या नाम है" in hi_q.question
    assert len(hi_q.helper_text) > 0

    # Marathi
    mr_q = get_fallback_question("business_name", "Business Name", "string", "Identify enterprise", "Bank requirement", None, "mr")
    assert "व्यवसायाचे किंवा उपक्रमाचे नाव काय आहे" in mr_q.question
    assert len(mr_q.helper_text) > 0


from app.services.dpr_stage1.dpr_registry import DPRReadinessStatus

@pytest.mark.asyncio
async def test_question_engine_prioritization_and_filtering():
    """Verify Question Engine picks highest priority gap and skips non-askable fields."""
    # Create synthetic gap analysis with a mix of blocking, non-blocking, and calculated fields
    gap_analysis = DPRGapAnalysisResult(
        total_fields=30,
        applicable_fields=25,
        resolved=20,
        benchmark_resolved=5,
        engine_resolved=10,
        user_resolved=5,
        derived=0,
        user_required=3,
        document_pending=0,
        unknown=2,
        not_applicable=5,
        blocking_gaps=[
            # A calculated field should be skipped even if listed in gaps
            GapItem(
                field_id="total_project_cost",
                section_id="sec_means_of_finance",
                module_id="mod_financial_plan",
                label="Total Project Cost",
                gap_category="CALCULATED_FIELD",
                resolution_path="ENGINE",
                materiality="CRITICAL",
                is_blocking=True,
                description="Project Cost total",
                why_required="Financial total",
                editable=False,
            ),
            # A genuine user gap
            GapItem(
                field_id="premises_status",
                section_id="sec_operating_premises",
                module_id="mod_technical_specs",
                label="Premises Status",
                gap_category="INTAKE_GAP",
                resolution_path="USER",
                materiality="HIGH",
                is_blocking=True,
                description="Operating premises status",
                why_required="Determine rent / lease / ownership outlay",
                editable=True,
            ),
        ],
        high_priority_gaps=[
            GapItem(
                field_id="promoter_education",
                section_id="sec_promoter_background",
                module_id="mod_promoter_profile",
                label="Promoter Education",
                gap_category="INTAKE_GAP",
                resolution_path="USER",
                materiality="MEDIUM",
                is_blocking=False,
                description="Educational qualification",
                why_required="Scheme eligibility check",
                editable=True,
            )
        ],
        optional_gaps=[],
        section_summaries={},
        module_summaries={},
        dpr_readiness_status=DPRReadinessStatus.DPR_INPUT_INCOMPLETE,
        can_proceed_to_dpr=False,
        readiness_reasons=["Gaps present"],
        critical_unresolved_count=1
    )

    dpr_context_package = {
        "scenario_id": "TEST-SCENARIO-1",
        "business_id": "BIZ-001",
        "business_profile": {"business_name": "Radha Handloom", "archetype": "retail"},
        "location_profile": {"district": "Varanasi"},
        "fields": {
            "total_project_cost": {"status": "RESOLVED_ENGINE", "value": 1200000.0},
            "premises_status": {"status": "USER_REQUIRED", "value": None},
            "promoter_education": {"status": "USER_REQUIRED", "value": None}
        },
        "user_language": "hi"
    }

    question = await dpr_question_engine.get_next_question(
        gap_analysis=gap_analysis,
        dpr_context_package=dpr_context_package,
        language="hi"
    )

    assert question is not None
    # Must select premises_status, NEVER total_project_cost
    assert question.field_id == "premises_status"
    assert question.language == "hi"
    assert question.question_type == "CHOICE"
    assert question.options is not None
    assert len(question.options) > 0
    assert question.resolution_trace is not None
