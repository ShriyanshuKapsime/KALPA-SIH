"""
Unit & Regression Test Suite for KALPA Stage 14.3 Type Safety & Invariant Verification.

Enforces strict separation of authoritative numeric types (raw float) and bank-facing display types (strings),
validating zero string vs float comparison errors in dpr_context_builder, document_schema, validation, and orchestrator.
"""
import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.dpr.stage14_3.document_schema import (
    safe_parse_numeric,
    extract_financial_scalars,
    build_dpr_final_data_package,
    DPR_FINAL_DATA_PACKAGE,
)
from app.dpr.stage14_3.document_assembler import DPRDocumentAssembler
from app.dpr.stage14_3.validation import DPRValidator
from app.dpr.stage14_3.narrative_validator import parse_indian_currency_number, DPRNarrativeValidator
from app.dpr.stage14_3 import (
    Stage14_3Orchestrator,
    DPRGenerationRequest,
    DPRStatus,
)
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    FieldResolutionStatus,
    resolve_field_semantically,
)
from app.services.dpr_stage1.dpr_context_builder import DPRContextBuilder, dpr_context_builder
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager


# -----------------------------------------------------------------------------
# 1. DSCR Raw vs Display Values
# -----------------------------------------------------------------------------
def test_dscr_raw_value_is_float():
    raw_fin = {
        "banking_metrics": {
            "average_dscr": "1.99x",
            "minimum_dscr": "1.75",
        }
    }
    scalars = extract_financial_scalars(raw_fin)
    assert isinstance(scalars["average_dscr"], float)
    assert scalars["average_dscr"] == 1.99
    assert isinstance(scalars["minimum_dscr"], float)
    assert scalars["minimum_dscr"] == 1.75


def test_dscr_display_value_is_string():
    pkg = DPR_FINAL_DATA_PACKAGE(
        business_id="test_biz",
        business_name="Test Enterprise",
        business_activity="Manufacturing",
        promoter_name="Test Promoter",
        average_dscr=1.99,
        minimum_dscr=1.75,
        total_project_cost=790000.0,
        term_loan=553000.0,
        promoter_contribution=237000.0,
    )
    fin_pkg = {"banking_metrics": {"average_dscr": 1.99, "minimum_dscr": 1.75}}
    placeholders = DPRDocumentAssembler.build_placeholder_map(pkg, fin_pkg)
    assert isinstance(placeholders["{{AVERAGE_DSCR}}"], str)
    assert placeholders["{{AVERAGE_DSCR}}"] == "1.99x"
    assert isinstance(placeholders["{{MIN_DSCR}}"], str)
    assert placeholders["{{MIN_DSCR}}"] == "1.75x"


# -----------------------------------------------------------------------------
# 2. Currency Raw vs Display Values
# -----------------------------------------------------------------------------
def test_currency_raw_value_is_numeric():
    raw_fin = {
        "project_cost": {
            "total_project_cost": "₹7,90,000",
            "plant_and_machinery": "₹ 5,00,000",
            "working_capital_margin": "₹ 90,000",
        },
        "means_of_finance": {
            "term_loan": "₹5,53,000",
            "promoter_contribution": "₹2,37,000",
        }
    }
    scalars = extract_financial_scalars(raw_fin)
    assert isinstance(scalars["total_project_cost"], float)
    assert scalars["total_project_cost"] == 790000.0
    assert isinstance(scalars["term_loan"], float)
    assert scalars["term_loan"] == 553000.0
    assert isinstance(scalars["promoter_contribution"], float)
    assert scalars["promoter_contribution"] == 237000.0


def test_currency_display_value_is_string():
    pkg = DPR_FINAL_DATA_PACKAGE(
        business_id="test_biz",
        business_name="Test Enterprise",
        business_activity="Manufacturing",
        promoter_name="Test Promoter",
        total_project_cost=790000.0,
        term_loan=553000.0,
        promoter_contribution=237000.0,
    )
    fin_pkg = {
        "total_project_cost": 790000.0,
        "means_of_finance": {
            "term_loan": 553000.0,
            "promoter_contribution": 237000.0
        }
    }
    placeholders = DPRDocumentAssembler.build_placeholder_map(pkg, fin_pkg)
    assert isinstance(placeholders["{{PROJECT_COST}}"], str)
    assert "₹" in placeholders["{{PROJECT_COST}}"]
    assert "7,90,000" in placeholders["{{PROJECT_COST}}"]
    assert isinstance(placeholders["{{TERM_LOAN}}"], str)
    assert "₹" in placeholders["{{TERM_LOAN}}"]
    assert "5,53,000" in placeholders["{{TERM_LOAN}}"]


# -----------------------------------------------------------------------------
# 3. Percentage Raw vs Display Values
# -----------------------------------------------------------------------------
def test_percentage_raw_value_is_numeric():
    raw_fin = {
        "banking_metrics": {
            "break_even_capacity_pct": "28.1%",
            "promoter_equity_pct": "30.0%",
        }
    }
    scalars = extract_financial_scalars(raw_fin)
    assert isinstance(scalars["break_even_utilization"], float)
    assert scalars["break_even_utilization"] == 28.1
    assert isinstance(scalars["promoter_margin_pct"], float)
    assert scalars["promoter_margin_pct"] == 30.0


def test_percentage_display_value_is_string():
    pkg = DPR_FINAL_DATA_PACKAGE(
        business_id="test_biz",
        business_name="Test Enterprise",
        business_activity="Manufacturing",
        promoter_name="Test Promoter",
        break_even_utilization=28.1,
    )
    fin_pkg = {"banking_metrics": {"break_even_capacity_pct": 28.1}}
    placeholders = DPRDocumentAssembler.build_placeholder_map(pkg, fin_pkg)
    assert isinstance(placeholders["{{BREAK_EVEN}}"], str)
    assert placeholders["{{BREAK_EVEN}}"] == "28.1%"


# -----------------------------------------------------------------------------
# 4. safe_parse_numeric robust parsing & No string vs float comparison
# -----------------------------------------------------------------------------
def test_no_string_float_comparison():
    assert safe_parse_numeric("1.99", 0.0) == 1.99
    assert safe_parse_numeric("1.99x", 0.0) == 1.99
    assert safe_parse_numeric("₹ 7,11,000", 0.0) == 711000.0
    assert safe_parse_numeric("25.0%", 0.0) == 25.0
    assert safe_parse_numeric("25.0% p.a.", 0.0) == 25.0
    assert safe_parse_numeric("7.11 lakh", 0.0) == 711000.0
    assert safe_parse_numeric("1.5 crore", 0.0) == 15000000.0
    assert safe_parse_numeric(None, 42.0) == 42.0
    assert safe_parse_numeric("UNKNOWN", 0.0) == 0.0
    assert safe_parse_numeric(123.45, 0.0) == 123.45


def test_no_mixed_numeric_lists():
    mixed_list = ["1.99", 2.5, "₹3.0", 1.2]
    parsed = [safe_parse_numeric(x, 0.0) for x in mixed_list]
    assert sorted(parsed) == [1.2, 1.99, 2.5, 3.0]
    assert min(parsed) == 1.2
    assert max(parsed) == 3.0


def test_min_dscr_numeric():
    fin_pkg = {
        "banking_metrics": {
            "average_dscr": "1.85",
            "dscr_y1": "1.52",
        }
    }
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["minimum_dscr"] == 1.52
    assert scalars["minimum_dscr"] > 1.20


def test_max_dscr_numeric():
    fin_pkg = {
        "banking_metrics": {
            "average_dscr": 2.10,
            "dscr_y1": 1.70,
            "dscr_y5": 2.45,
        }
    }
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["average_dscr"] == 2.10
    assert max([scalars["minimum_dscr"], scalars["average_dscr"]]) == 2.10


def test_break_even_numeric():
    fin_pkg = {"banking_metrics": {"break_even_capacity_pct": "34.5%"}}
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["break_even_utilization"] == 34.5
    assert scalars["break_even_utilization"] <= 70.0


def test_project_cost_numeric():
    fin_pkg = {
        "total_project_cost": "₹ 12,00,000",
        "project_cost": {
            "plant_and_machinery": "800000",
            "land_and_building": "200000",
            "working_capital_margin": "200000",
        }
    }
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["total_project_cost"] == 1200000.0
    assert scalars["plant_machinery"] == 800000.0


def test_loan_numeric():
    fin_pkg = {"means_of_finance": {"term_loan": "₹8,40,000"}}
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["term_loan"] == 840000.0


def test_promoter_contribution_numeric():
    fin_pkg = {"means_of_finance": {"promoter_contribution": "₹3,60,000"}}
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["promoter_contribution"] == 360000.0


def test_unknown_not_coerced_to_zero():
    # UNKNOWN should remain distinct from zero in text contexts
    val = "UNKNOWN"
    # When numeric parsing is explicitly requested, default is preserved
    parsed = safe_parse_numeric(val, default=-1.0)
    assert parsed == -1.0


def test_none_optional_numeric_safe():
    fin_pkg = {
        "project_cost": {},
        "means_of_finance": {},
    }
    scalars = extract_financial_scalars(fin_pkg)
    assert scalars["total_project_cost"] == 0.0
    assert isinstance(scalars["average_dscr"], float)
    assert scalars["average_dscr"] >= 0.0


# -----------------------------------------------------------------------------
# 5. Narrative Claim Normalization & Currency Parser
# -----------------------------------------------------------------------------
def test_narrative_numeric_claim_normalization():
    assert parse_indian_currency_number("₹7,11,000") == 711000.0
    assert parse_indian_currency_number("7.11 lakh") == 711000.0
    assert parse_indian_currency_number("1.5 crore") == 15000000.0
    assert parse_indian_currency_number("500000") == 500000.0
    assert parse_indian_currency_number("Proprietorship") is None


def test_formatted_currency_never_enters_financial_engine():
    fin_pkg = {
        "total_project_cost": "₹ 7,90,000",
        "means_of_finance": {
            "total_funding": "₹ 7,90,000",
            "promoter_contribution": "₹ 2,37,000",
            "term_loan": "₹ 5,53,000",
            "promoter_margin_pct": "30.0%",
        },
        "project_cost": {
            "total_project_cost": "₹ 7,90,000",
            "plant_and_machinery": "₹ 7,00,000",
            "working_capital_margin": "₹ 90,000",
        },
        "banking_metrics": {
            "average_dscr": "1.99x",
            "minimum_dscr": "1.75x",
            "break_even_capacity_pct": "28.1%",
        },
        "profit_and_loss": [
            {"gross_revenue": "₹ 15,00,000", "pat": "₹ 2,50,000"}
        ]
    }
    # Validate with formatted strings directly
    is_valid, errors = DPRValidator.validate_dpr_financial_integrity(fin_pkg)
    assert is_valid is True
    assert len(errors) == 0


def test_dpr_final_package_validation():
    fin_pkg = {
        "total_project_cost": 790000.0,
        "means_of_finance": {
            "total_funding": 790000.0,
            "promoter_contribution": 237000.0,
            "term_loan": 553000.0,
            "promoter_margin_pct": 30.0,
        },
        "project_cost": {
            "total_project_cost": 790000.0,
            "plant_and_machinery": 700000.0,
            "working_capital_margin": 90000.0,
        },
        "banking_metrics": {
            "average_dscr": 1.99,
            "minimum_dscr": 1.75,
            "break_even_capacity_pct": 28.1,
            "first_year_pat": 250000.0,
        },
        "profit_and_loss": [
            {"gross_revenue": 1500000.0, "pat": 250000.0}
        ]
    }
    summary = DPRValidator.run_financial_integrity_checks(fin_pkg)
    assert summary.overall_status in ("PASS", "WARNING")
    assert summary.failed_count == 0


# -----------------------------------------------------------------------------
# 6. Context Builder Confidence String Normalization (Root Cause 1)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_context_builder_confidence_string_normalization():
    # Test semantic resolver with string confidence values in previous_fields
    sources = {
        "business_profile": {
            "name": "Ganga Dairy",
            "business_name": "Ganga Dairy"
        },
        "previous_fields": {
            "business_name": {
                "value": "Ganga Dairy",
                "status": "RESOLVED_UPSTREAM",
                "confidence": "CONFIRMED",
                "source_type": "UPSTREAM_STAGE",
                "source_id": "STAGE1_INTAKE",
                "source_reference": "Intake Form"
            },
            "nic_code": {
                "value": "01411",
                "status": "RESOLVED_BENCHMARK",
                "confidence": "ESTIMATED",
                "source_type": "BENCHMARK_MODEL",
                "source_id": "STAGE2_CLASSIFICATION",
                "source_reference": "Benchmark Database"
            }
        }
    }
    res = resolve_field_semantically(field_id="business_name", sources=sources)
    assert res["value"] == "Ganga Dairy"
    assert isinstance(res["confidence"], float)
    assert res["confidence"] >= 0.8

    res2 = resolve_field_semantically(field_id="nic_code", sources=sources)
    assert res2["value"] == "01411"
    assert isinstance(res2["confidence"], float)
    assert res2["confidence"] >= 0.5


# -----------------------------------------------------------------------------
# 7. End-to-End Stage 14.3 Dairy DPR Generation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_dairy_dpr_stage14_3_end_to_end_generation():
    biz_id = "test_type_safety_dairy"
    scen = dpr_scenario_manager.get_or_create_scenario(biz_id)

    # Set canonical answers
    for fid, ans in [
        ("business_name", "Ganga Dairy & Livestock Unit"),
        ("business_activity", "Commercial Dairy Farming and Milk Production"),
        ("promoter_name", "Suresh Patil"),
        ("nic_code", "01411"),
        ("target_state", "Maharashtra"),
        ("target_district", "Kolhapur"),
        ("legal_constitution", "PROPRIETORSHIP"),
        ("premises_status", "OWNED"),
        ("carpet_area", 1500.0),
        ("promoter_experience_years", 8.0),
        ("promoter_education", "GRADUATE"),
    ]:
        dpr_scenario_manager.set_user_answer(
            business_id=biz_id,
            field_id=fid,
            value=ans,
            scenario_id=scen.scenario_id
        )

    req = DPRGenerationRequest(
        business_id=biz_id,
        scenario_id=scen.scenario_id,
        format="pdf",
        language="en",
        regenerate_narrative=False
    )

    orchestrator = Stage14_3Orchestrator()
    resp = await orchestrator.generate_dpr(req)

    assert resp.status == "COMPLETED"
    assert resp.page_count >= 20
    assert resp.dpr_status in (DPRStatus.BANK_REVIEW_READY, DPRStatus.READY_FOR_SUBMISSION, DPRStatus.DRAFT_DPR)
    assert resp.financial_integrity.failed_count == 0
