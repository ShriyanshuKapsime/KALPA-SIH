"""
Milestone 6: Bankable DPR Financial Packager Test Suite.
Validates:
- Deterministic packaging with zero metric recalculation
- UNKNOWN != ZERO enforcement
- Upstream provenance preservation (M1–M5)
- Standardized 18-section DPR structure
- CMA statements and data completeness audit
- API / DPR generation / PDF rendering end-to-end integration
"""
import os
import pytest
from datetime import datetime

from app.services.financial_engine import financial_engine
from app.services.financial_engine.dpr_packager import (
    dpr_packager,
    DPRFinancialPackage,
    CompletenessStatus,
    ProvenanceTag,
    format_inr,
    format_inr_lakhs,
    format_percentage,
    format_ratio,
    format_year_label,
)
from app.engines.dpr.service import dpr_generation_engine
from app.engines.dpr.pdf_generator import dpr_pdf_generator, REPORTLAB_AVAILABLE
from app.engines.dpr.schemas import DPRDocumentRequest


@pytest.fixture
def standard_financial_analysis():
    """Executes deterministic M1-M5 financial analysis for testing."""
    payload = {
        "analysis_id": "test_m6_analysis_001",
        "session_id": "test_m6_session_001",
        "business_profile": {
            "business_id": "biz_m6_test",
            "specific_business": "Poultry Broiler Commercial Unit",
            "business_category": "AGRI_ALLIED",
            "nic_code": "01461",
        },
        "financial_profile": {
            "available_margin_capital": 100000.0,
            "preferred_project_cost": 1000000.0,
        },
        "beneficiary_profile": {
            "beneficiary_category": "OBC",
            "gender": "Female",
            "is_greenfield": True,
        },
        "location_profile": {
            "district": "Pune",
            "state": "Maharashtra",
        },
    }
    return financial_engine.analyze(payload)


# -----------------------------------------------------------------------------
# 1. Complete M1–M5 Package Packaging & Schema Validation
# -----------------------------------------------------------------------------
def test_complete_m1_m5_package(standard_financial_analysis):
    container = standard_financial_analysis.financial_analysis
    pkg = container.dpr_financial_package

    assert isinstance(pkg, DPRFinancialPackage)
    assert pkg.project_identity.project_name == "Poultry Broiler Commercial Unit"
    assert pkg.project_identity.business_id == "biz_m6_test"
    assert pkg.project_cost.total_project_cost is not None
    assert pkg.means_of_finance.promoter_contribution in (100000.0, 61000.0)
    assert pkg.means_of_finance.term_loan is not None
    assert pkg.means_of_finance.term_loan > 0
    assert pkg.means_of_finance.is_gap_eliminated is True

    # 18 Standard Sections
    assert len(pkg.sections) == 18
    section_codes = [s.section_code for s in pkg.sections]
    assert "SEC_01_EXEC_SUMMARY" in section_codes
    assert "SEC_02_PROJECT_COST" in section_codes
    assert "SEC_03_MEANS_OF_FINANCE" in section_codes
    assert "SEC_06_PROFIT_LOSS" in section_codes
    assert "SEC_07_BALANCE_SHEET" in section_codes
    assert "SEC_10_LOAN_REPAYMENT" in section_codes
    assert "SEC_12_DSCR_RATIOS" in section_codes
    assert "SEC_13_STRESS_SENSITIVITY" in section_codes
    assert "SEC_17_EVIDENCE_PROVENANCE" in section_codes
    assert "SEC_18_VALIDATION_COMPLETENESS" in section_codes


# -----------------------------------------------------------------------------
# 2. UNKNOWN != ZERO Enforcement
# -----------------------------------------------------------------------------
def test_unknown_not_zero_preservation():
    """Ensures None/UNKNOWN upstream values are NEVER replaced with 0.0."""
    partial_container = {
        "project_financing": {
            "available_margin": None,
            "theoretical_project_cost": None,
            "estimated_financeable_loan": None,
        },
        "capital_structure": {
            "total_project_cost": None,
            "fixed_capital_capex": None,
            "working_capital": None,
        },
        "loan_management": {
            "principal": None,
            "monthly_emi": None,
            "annual_interest_rate": None,
            "tenure_months": 84,
        },
    }

    pkg = dpr_packager.package(
        analysis_response_or_container=partial_container,
        package_id="test_partial_pkg",
    )

    # UNKNOWN values must remain None, not 0.0
    assert pkg.project_cost.total_project_cost is None
    assert pkg.project_cost.plant_and_machinery is None
    assert pkg.means_of_finance.promoter_contribution is None
    assert pkg.means_of_finance.term_loan is None
    assert pkg.loan_structure.monthly_emi is None


# -----------------------------------------------------------------------------
# 3. Explicit Zero Preserved
# -----------------------------------------------------------------------------
def test_explicit_zero_preserved():
    """Explicit 0 must remain 0 and not be treated as UNKNOWN."""
    zero_container = {
        "project_financing": {
            "available_margin": 0.0,
            "excess_margin": 0.0,
            "theoretical_project_cost": 500000.0,
            "estimated_financeable_loan": 500000.0,
        },
        "capital_structure": {
            "total_project_cost": 500000.0,
            "fixed_capital_capex": 500000.0,
            "working_capital": 0.0,
            "margin_contribution": 0.0,
            "loan_component": 500000.0,
        },
        "loan_management": {
            "principal": 500000.0,
            "moratorium_months": 0,
            "moratorium_interest_total": 0.0,
            "monthly_emi": 8500.0,
            "total_interest": 100000.0,
            "total_repayment": 600000.0,
            "annual_interest_rate": 0.09,
            "tenure_months": 60,
        },
    }

    pkg = dpr_packager.package(
        analysis_response_or_container=zero_container,
        package_id="test_zero_pkg",
    )

    assert pkg.means_of_finance.promoter_contribution == 0.0
    assert pkg.project_cost.working_capital_margin == 0.0
    assert pkg.loan_structure.moratorium_months == 0


# -----------------------------------------------------------------------------
# 4. Provenance Preservation
# -----------------------------------------------------------------------------
def test_provenance_preservation(standard_financial_analysis):
    pkg = standard_financial_analysis.financial_analysis.dpr_financial_package

    assert pkg.project_cost.provenance_tag == ProvenanceTag.PACKAGED_FROM_M2.value
    assert pkg.means_of_finance.provenance_tag == ProvenanceTag.PACKAGED_FROM_M3.value
    assert pkg.projected_financial_statements.provenance_tag == ProvenanceTag.PACKAGED_FROM_M3.value
    assert pkg.banking_metrics.provenance_tag == ProvenanceTag.PACKAGED_FROM_M4.value
    assert pkg.m5_stress_appraisal.provenance_tag == ProvenanceTag.PACKAGED_FROM_M5.value


# -----------------------------------------------------------------------------
# 5. Upstream Values Passed Unchanged (No Recalculation)
# -----------------------------------------------------------------------------
def test_upstream_values_passed_unchanged(standard_financial_analysis):
    container = standard_financial_analysis.financial_analysis
    pkg = container.dpr_financial_package

    # Project Cost & Funding
    assert pkg.project_cost.total_project_cost == container.capital_structure.total_project_cost
    assert pkg.means_of_finance.promoter_contribution == container.capital_structure.margin_contribution
    assert pkg.means_of_finance.term_loan == container.capital_structure.loan_component

    # Loan Management
    assert pkg.loan_structure.sanctioned_loan_amount == container.loan_management.principal
    assert pkg.loan_structure.monthly_emi == container.loan_management.monthly_emi
    assert pkg.loan_structure.total_interest_payable == container.loan_management.total_interest

    # Banking Metrics & DSCR
    bep_sales = container.break_even.annual_break_even_revenue or container.break_even.monthly_break_even_revenue
    expected_dscr = getattr(getattr(container, "banking_appraisal", None), "dscr", None)
    expected_dscr_val = getattr(expected_dscr, "average_dscr", None) or container.debt_service.dscr
    assert pkg.banking_metrics.average_dscr == expected_dscr_val
    assert pkg.banking_metrics.break_even_sales_amount == pytest.approx(bep_sales, abs=1.0)
    assert pkg.banking_metrics.break_even_capacity_pct == pytest.approx(container.break_even.break_even_utilization_pct, abs=0.5)


# -----------------------------------------------------------------------------
# 6. Incomplete Package Detection
# -----------------------------------------------------------------------------
def test_incomplete_package_detection():
    sparse_container = {
        "project_financing": {},
        "capital_structure": {},
    }
    pkg = dpr_packager.package(
        analysis_response_or_container=sparse_container,
        package_id="test_sparse_pkg",
    )

    completeness = pkg.data_completeness
    assert completeness.status in [CompletenessStatus.INCOMPLETE, CompletenessStatus.PARTIALLY_COMPLETE]
    assert len(completeness.unresolved_fields) > 0
    assert completeness.resolved_fields < completeness.required_fields_total


# -----------------------------------------------------------------------------
# 7. Centralized Formatting Helpers (INR, %, Ratio, UNKNOWN)
# -----------------------------------------------------------------------------
def test_formatting_helpers():
    # INR Formatting (Default 2 decimals)
    assert format_inr(1000000.0) == "₹10,00,000.00"
    assert format_inr(1000000.0, decimals=0) == "₹10,00,000"
    assert format_inr(15420.5) == "₹15,420.50"
    assert format_inr(0.0) == "₹0.00"
    assert format_inr(None) == "Not available"
    assert format_inr(-25000.0, accounting_brackets=True) == "(₹25,000.00)"

    # INR Lakhs
    assert format_inr_lakhs(1000000.0) == "₹10.00 Lakhs"
    assert format_inr_lakhs(None) == "Not available"

    # Percentage Formatting
    assert format_percentage(8.0) == "8.0%"
    assert format_percentage(0.08, multiply_by_100=True) == "8.0%"
    assert format_percentage(8.5) == "8.5%"
    assert format_percentage(0.0) == "0.0%"
    assert format_percentage(None) == "Not available"

    # Ratio Formatting
    assert format_ratio(1.65) == "1.65x"
    assert format_ratio(None) == "Not available"

    # Year Label
    assert format_year_label(1) == "Year 1 (FY 2026-27)"


# -----------------------------------------------------------------------------
# 8. Repayment Schedule Formatting & Amortization Preservation
# -----------------------------------------------------------------------------
def test_repayment_schedule_preservation(standard_financial_analysis):
    container = standard_financial_analysis.financial_analysis
    pkg = container.dpr_financial_package

    # If repayment schedule is populated in M3/core, it must appear in loan_structure
    if container.repayment and container.repayment.monthly_schedule:
        assert len(pkg.loan_structure.monthly_schedule) == len(container.repayment.monthly_schedule)
        first_orig = container.repayment.monthly_schedule[0]
        first_pkg = pkg.loan_structure.monthly_schedule[0]
        assert first_pkg.period == first_orig.period
        assert first_pkg.payment == first_orig.payment
        assert first_pkg.principal_component == first_orig.principal_component
        assert first_pkg.interest_component == first_orig.interest_component
        # Also accessible via repayment_schedule alias
        assert len(pkg.loan_structure.repayment_schedule) == len(container.repayment.monthly_schedule)


# -----------------------------------------------------------------------------
# 9. DPR Generation Pipeline Integration
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_dpr_generation_pipeline(standard_financial_analysis):
    container = standard_financial_analysis.financial_analysis
    pkg = container.dpr_financial_package

    request = DPRDocumentRequest(
        business_id="biz_m6_test",
        session_id="test_m6_session_001",
        analysis_id="test_m6_analysis_001",
        financial_package=pkg,
        non_financial_context={
            "market_demand": "High demand in urban fringe",
            "swot": {"strengths": ["Strong technical promoter", "Proximity to market"]},
        },
    )

    metadata = await dpr_generation_engine.generate_dpr(request, db=None)

    assert metadata.document_id.startswith("dpr-biz_m6_test")
    assert metadata.file_format == "pdf"
    assert metadata.status in ["generated", "incomplete_draft"]
    assert metadata.file_path is not None
    assert metadata.financial_highlights["total_project_cost"] == pkg.project_cost.total_project_cost
    assert metadata.financial_highlights["term_loan"] == pkg.loan_structure.sanctioned_loan_amount
    assert metadata.financial_highlights["monthly_emi"] == pkg.loan_structure.monthly_emi
    assert metadata.dpr_package is not None


# -----------------------------------------------------------------------------
# 10. PDF Generator Smoke Test
# -----------------------------------------------------------------------------
@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="ReportLab is not installed in the environment")
def test_pdf_generation_smoke(standard_financial_analysis):
    pkg = standard_financial_analysis.financial_analysis.dpr_financial_package
    pdf_bytes = dpr_pdf_generator.generate_pdf(
        financial_package=pkg,
        non_financial_context={"market": "Verified poultry sector demand"},
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


# -----------------------------------------------------------------------------
# 11. Final End-to-End Traceability Test (Requirement 16)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_end_to_end_traceability():
    """
    Full pipeline test:
    Structured business profile → M1 → M2 → M3 → M4 → M5 → M6 → DPR payload → PDF generation input.
    Asserts authoritative calculated values appear completely unchanged throughout.
    """
    raw_input = {
        "analysis_id": "e2e_traceability_001",
        "session_id": "e2e_session_001",
        "business_profile": {
            "business_id": "biz_e2e_bakery",
            "specific_business": "Artisanal Bakery & Confectionery",
            "business_category": "FOOD_PROCESSING",
            "nic_code": "10712",
        },
        "financial_profile": {
            "available_margin_capital": 250000.0,
            "preferred_project_cost": 2500000.0,
        },
        "beneficiary_profile": {
            "beneficiary_category": "GENERAL",
            "gender": "Male",
            "is_greenfield": True,
        },
        "location_profile": {
            "district": "Bangalore Urban",
            "state": "Karnataka",
        },
    }

    # Step 1: Execute Financial Engine
    resp = financial_engine.analyze(raw_input)
    fin_container = resp.financial_analysis

    # Step 2: Extract M6 Canonical Package
    m6_package = fin_container.dpr_financial_package
    assert m6_package is not None

    # Verify calculated upstream values match unchanged in M6:
    cost_upstream = fin_container.capital_structure.total_project_cost
    margin_upstream = fin_container.capital_structure.margin_contribution
    loan_upstream = fin_container.loan_management.principal
    emi_upstream = fin_container.loan_management.monthly_emi
    dscr_upstream = getattr(getattr(fin_container, "banking_appraisal", None), "dscr", None)
    dscr_upstream_val = getattr(dscr_upstream, "average_dscr", None) or fin_container.debt_service.dscr
    bep_sales_upstream = fin_container.break_even.annual_break_even_revenue or fin_container.break_even.monthly_break_even_revenue

    assert m6_package.project_cost.total_project_cost == cost_upstream
    assert m6_package.means_of_finance.promoter_contribution == margin_upstream
    assert m6_package.loan_structure.sanctioned_loan_amount == loan_upstream
    assert m6_package.loan_structure.monthly_emi == emi_upstream
    assert m6_package.banking_metrics.average_dscr == dscr_upstream_val
    assert m6_package.banking_metrics.break_even_sales_amount == pytest.approx(bep_sales_upstream, abs=1.0)

    # Step 3: Pass into DPR Generation Engine
    dpr_req = DPRDocumentRequest(
        business_id="biz_e2e_bakery",
        session_id="e2e_session_001",
        analysis_id="e2e_traceability_001",
        financial_package=m6_package,
    )
    dpr_result = await dpr_generation_engine.generate_dpr(dpr_req, db=None)

    # Step 4: Verify DPR Output retains exact values
    highlights = dpr_result.financial_highlights
    assert highlights["total_project_cost"] == cost_upstream
    assert highlights["promoter_contribution"] == margin_upstream
    assert highlights["term_loan"] == loan_upstream
    assert highlights["monthly_emi"] == emi_upstream
    assert highlights["average_dscr"] == dscr_upstream_val
    assert highlights["break_even_sales_amount"] == pytest.approx(bep_sales_upstream, abs=1.0)

    # Step 5: Verify PDF Generation input receives complete package and succeeds
    if REPORTLAB_AVAILABLE:
        pdf_bytes = dpr_pdf_generator.generate_pdf(
            financial_package=m6_package,
            non_financial_context={"market_opportunity": "Growing demand for organic bakery items"},
        )
        assert len(pdf_bytes) > 2000
        assert pdf_bytes.startswith(b"%PDF")


# -----------------------------------------------------------------------------
# 12. API Integration Test for /dpr-package endpoint
# -----------------------------------------------------------------------------
def test_api_dpr_package_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "analysis_id": "api_test_001",
        "business_profile": {
            "business_id": "biz_api_test",
            "specific_business": "Cold Storage Unit",
        },
        "financial_profile": {
            "available_margin_capital": 200000.0,
        },
    }
    response = client.post("/api/v1/financial-analysis/dpr-package", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_identity"]["project_name"] == "Cold Storage Unit"
    assert "project_cost" in data
    assert "means_of_finance" in data
    assert "banking_metrics" in data
    assert "sections" in data
    assert len(data["sections"]) == 18

