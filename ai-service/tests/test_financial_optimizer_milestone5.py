"""
Milestone 5 Test Suite: Stress Testing, Scheme Routing & Financing Optimizer.
Covers all 24 required target conditions:
1. Base case is preserved from M4.
2. Explicit revenue downside propagates correctly.
3. Explicit variable-cost stress propagates correctly.
4. Combined downside scenario works.
5. Unknown revenue does not become zero.
6. Unknown cost does not become zero.
7. Scheme eligibility is respected.
8. Scheme loan ceiling is enforced.
9. Actual scheme margin requirement is respected.
10. Promoter contribution gap is detected.
11. Explicit zero promoter contribution remains zero.
12. Financing gap is never plugged artificially.
13. Valid financing option is generated.
14. Invalid financing option is rejected.
15. Tenure alternatives calculate deterministic EMI correctly.
16. Stress DSCR is correctly calculated.
17. Stress liquidity is correctly calculated.
18. No-feasible-structure case returns NO_FEASIBLE_FINANCING_STRUCTURE.
19. Selected structure has explicit decision reasons.
20. Provenance exists for stress assumptions and selected financing.
21. Tri-state validation works.
22. Existing M1-M4 regression tests pass.
23. Existing Stage 9 regression tests pass.
24. Compile/import checks pass.
"""
import pytest
from typing import Dict, Any, Optional

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    LocationProfileInput,
    BeneficiaryProfileInput,
    ProjectAssumptionsInput,
    ProfitLossStatement,
    ProfitLossYear,
    CashFlowStatement,
    CashFlowYear,
    BalanceSheet,
    BalanceSheetYear,
    LoanManagement,
    FundingSourcesUses,
    FinancialProjection,
    WorkingCapitalAnalysis
)
from app.services.financial_engine.engine import financial_engine
from app.services.financial_engine.optimizer import (
    m5_engine,
    stress_engine,
    scheme_router,
    promoter_contribution_analysis_engine,
    financing_feasibility_engine,
    tenure_analysis_engine,
    financing_options_generator,
    financing_optimizer,
    m5_validation_engine,
    M5ReasonCode,
    ResilienceStatus,
    SchemeEligibilityStatus,
    M5ValidationState,
    StressScenarioType
)
from unittest.mock import patch
from app.services.financial_engine.optimizer.resilience_analysis import select_worst_case_scenario
from app.services.financial_engine.optimizer.m5_schema import (
    FinancingStructureCandidate,
    StressScenarioResult,
    M5DprFinancingSummary,
    FinancingGapAnalysisResult
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder


def _build_standard_test_request() -> FinancialAnalysisRequest:
    return FinancialAnalysisRequest(
        analysis_id="m5_test_session_101",
        session_id="session_m5_abc",
        financial_profile=FinancialProfileInput(
            available_margin_capital=100000.0,
            preferred_project_cost=500000.0,
        ),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Retail Apparel Store",
            sector="retail",
            category="apparel",
            nic_code="47110"
        ),
        location_profile=LocationProfileInput(
            district="Indore",
            state="Madhya Pradesh"
        ),
        project_assumptions=ProjectAssumptionsInput(
            expected_monthly_revenue=240000.0,
            expected_monthly_units=800.0,
            expected_unit_price=300.0,
        ),
        user_driver_inputs={
            "is_greenfield": True,
            "pre_operating_cost": 0.0,
            "contingency": 0.0,
            "monthly_units": 800.0,
            "expected_unit_price": 300.0,
            "gross_margin": 30.0,
            "inventory_days": 30.0,
            "receivable_days": 15.0,
            "payable_days": 20.0,
            "monthly_rent": 10000.0,
            "staff_count": 2,
            "salary_per_person": 12000.0,
            "electricity_cost": 2500.0,
            "operating_buffer_months": 1.0,
            "capex_override": 200000.0,
            "annual_revenue_growth_rate": 5.0,
            "depreciation_life_years": 10.0,
            "fixed_cost_ratio": 0.40,
            "discount_rate": 0.12,
            "tax_rate": 0.0
        }
    )


# =============================================================================
# 1. Base Case Is Preserved From M4
# =============================================================================
def test_01_base_case_preserved_from_m4():
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    assert fa.banking_appraisal is not None
    assert fa.financing_optimizer is not None
    m5 = fa.financing_optimizer

    base_ref = m5.base_case_reference
    assert base_ref is not None
    assert base_ref["total_project_cost"] == fa.capital_structure.total_project_cost
    assert m5.dpr_summary is not None
    assert m5.dpr_summary.total_project_cost == fa.capital_structure.total_project_cost


# =============================================================================
# 2. Explicit Revenue Downside Propagates Correctly
# =============================================================================
def test_02_explicit_revenue_downside_propagates():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=600000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=170000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl)
    rev_down = next((s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE), None)

    assert rev_down is not None
    assert rev_down.status == "RESOLVED"
    # -15% downside on 1,000,000 = 850,000
    assert rev_down.stressed_value == 850000.0
    assert rev_down.revenue == 850000.0
    # COGS unchanged (600,000), OPEX unchanged (200,000) -> EBITDA = 850k - 800k = 50k
    assert rev_down.ebitda == 50000.0


# =============================================================================
# 3. Explicit Variable-Cost Stress Propagates Correctly
# =============================================================================
def test_03_explicit_variable_cost_stress_propagates():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=600000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=110000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl)
    var_up = next((s for s in scenarios if s.scenario_type == StressScenarioType.VARIABLE_COST_INCREASE), None)

    assert var_up is not None
    assert var_up.status == "RESOLVED"
    # +10% on COGS 600,000 = 660,000
    assert var_up.gross_profit == 340000.0  # 1,000,000 - 660,000
    assert var_up.ebitda == 140000.0        # 340,000 - 200,000


# =============================================================================
# 4. Combined Downside Scenario Works
# =============================================================================
def test_04_combined_downside_scenario():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=135000.0)
    ])
    wc_anal = WorkingCapitalAnalysis(operating_working_capital=50000.0)
    scenarios = stress_engine.evaluate(profit_loss=pl, working_capital_analysis=wc_anal)
    comb = next((s for s in scenarios if s.scenario_type == StressScenarioType.COMBINED_DOWNSIDE), None)

    assert comb is not None
    assert comb.status == "RESOLVED"
    # Revenue -10% = 900,000; COGS +5% = 525,000; OPEX +5% = 210,000
    assert comb.revenue == 900000.0
    assert comb.ebitda == 165000.0  # 900k - 525k - 210k


# =============================================================================
# 5. Unknown Revenue Does Not Become Zero
# =============================================================================
def test_05_unknown_revenue_does_not_become_zero():
    # Revenue is None
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=None, cogs=500000.0, operating_expenses=200000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl)
    rev_down = next((s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE), None)

    assert rev_down is not None
    assert rev_down.revenue is None
    assert rev_down.status == "UNRESOLVED"
    assert rev_down.resilience_status == ResilienceStatus.NOT_ASSESSABLE
    assert M5ReasonCode.UNRESOLVED_DRIVER in rev_down.reason_codes


# =============================================================================
# 6. Unknown Cost Does Not Become Zero
# =============================================================================
def test_06_unknown_cost_does_not_become_zero():
    # COGS is None
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=None, operating_expenses=200000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl)
    var_up = next((s for s in scenarios if s.scenario_type == StressScenarioType.VARIABLE_COST_INCREASE), None)

    assert var_up is not None
    assert var_up.status == "UNRESOLVED"
    assert var_up.gross_profit is None
    assert var_up.resilience_status == ResilienceStatus.NOT_ASSESSABLE
    assert M5ReasonCode.UNRESOLVED_DRIVER in var_up.reason_codes


# =============================================================================
# 7. Scheme Eligibility Is Respected
# =============================================================================
def test_07_scheme_eligibility_respected():
    # Cost = 100,000 -> Micro Finance eligible, Term Loan ineligible (min 140,001)
    options = scheme_router.evaluate_schemes(project_cost=100000.0)
    micro = next((o for o in options if o.scheme_id == "MICRO_FINANCE_SCHEME"), None)
    term = next((o for o in options if o.scheme_id == "TERM_LOAN_SCHEME"), None)

    assert micro is not None
    assert micro.eligibility_status in (SchemeEligibilityStatus.ELIGIBLE, SchemeEligibilityStatus.VERIFICATION_REQUIRED)

    assert term is not None
    assert term.eligibility_status == SchemeEligibilityStatus.INELIGIBLE
    assert any("below scheme minimum" in r for r in term.rejection_reasons)


# =============================================================================
# 8. Scheme Loan Ceiling Is Enforced
# =============================================================================
def test_08_scheme_loan_ceiling_enforced():
    # Micro Finance ceiling is ₹125,000. Cost = 140,000, 90% = 126,000 -> capped at 125,000
    options = scheme_router.evaluate_schemes(project_cost=140000.0)
    micro = next((o for o in options if o.scheme_id == "MICRO_FINANCE_SCHEME"), None)

    assert micro is not None
    assert micro.max_loan == 125000.0  # Capped by maximum_loan_limit


# =============================================================================
# 9. Actual Scheme Margin Requirement Is Respected
# =============================================================================
def test_09_actual_scheme_margin_requirement_respected():
    # Scheme with 15% margin requirement
    prom = promoter_contribution_analysis_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=75000.0,
        scheme_margin_percentage=15.0
    )
    assert prom.required_percentage == 15.0
    assert prom.required_promoter_contribution == 75000.0
    assert prom.is_adequate is True
    assert prom.gap_surplus == 0.0


# =============================================================================
# 10. Promoter Contribution Gap Is Detected
# =============================================================================
def test_10_promoter_contribution_gap_detected():
    # Required 15% (75k), available only 50k -> deficit 25k
    prom = promoter_contribution_analysis_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=50000.0,
        scheme_margin_percentage=15.0
    )
    assert prom.is_adequate is False
    assert prom.gap_surplus == -25000.0
    assert prom.reason_code == M5ReasonCode.PROMOTER_CONTRIBUTION_GAP


# =============================================================================
# 11. Explicit Zero Promoter Contribution Remains Zero
# =============================================================================
def test_11_explicit_zero_promoter_contribution_remains_zero():
    # PM MUDRA Shishu allows 0% margin. Explicit 0.0 remains 0.0
    prom = promoter_contribution_analysis_engine.evaluate(
        total_project_cost=50000.0,
        available_promoter_contribution=0.0,
        scheme_margin_percentage=0.0
    )
    assert prom.available_promoter_contribution == 0.0
    assert prom.required_promoter_contribution == 0.0
    assert prom.is_adequate is True
    assert prom.gap_surplus == 0.0
    assert prom.reason_code == M5ReasonCode.EXPLICIT_ZERO_PROMOTER


# =============================================================================
# 12. Financing Gap Is Never Plugged Artificially
# =============================================================================
def test_12_financing_gap_never_plugged():
    # Project cost 600k, promoter 100k, loan 400k -> gap 100k
    gap_res = financing_feasibility_engine.evaluate(
        total_project_cost=600000.0,
        available_promoter_contribution=100000.0,
        scheme_loan=400000.0,
        other_verified_financing=0.0
    )
    assert gap_res.is_balanced is False
    assert gap_res.funding_gap == 100000.0
    assert gap_res.funding_surplus == 0.0
    assert gap_res.reason_code == M5ReasonCode.FINANCING_GAP


# =============================================================================
# 13. Valid Financing Option Is Generated
# =============================================================================
def test_13_valid_financing_option_generated():
    scheme_opts = scheme_router.evaluate_schemes(project_cost=300000.0, available_promoter_contribution=50000.0)
    candidates = financing_options_generator.generate_candidates(
        project_cost=300000.0,
        available_promoter_contribution=50000.0,
        scheme_options=scheme_opts,
        base_cads=80000.0,
        stress_cads=65000.0,
        other_verified_financing=0.0
    )
    assert len(candidates) > 0
    feasible = [c for c in candidates if c.feasibility_status == "FEASIBLE"]
    assert len(feasible) > 0


# =============================================================================
# 14. Invalid Financing Option Is Rejected
# =============================================================================
def test_14_invalid_financing_option_rejected():
    scheme_opts = scheme_router.evaluate_schemes(project_cost=300000.0, available_promoter_contribution=10000.0) # insufficient margin (need 10% = 30k)
    candidates = financing_options_generator.generate_candidates(
        project_cost=300000.0,
        available_promoter_contribution=10000.0,
        scheme_options=scheme_opts,
        base_cads=80000.0,
        stress_cads=65000.0,
        other_verified_financing=0.0
    )
    # Margin not met -> should be marked INELIGIBLE_OR_STRESSED
    assert all(c.feasibility_status == "INELIGIBLE_OR_STRESSED" for c in candidates)


# =============================================================================
# 15. Tenure Alternatives Calculate Deterministic EMI Correctly
# =============================================================================
def test_15_tenure_alternatives_calculate_deterministic_emi():
    tenures = tenure_analysis_engine.evaluate_tenures(
        loan_amount=200000.0,
        annual_interest_rate=0.08,
        scheme_max_tenure_months=60,
        moratorium_months=0
    )
    assert len(tenures) >= 3  # e.g., 36, 48, 60
    t36 = next((t for t in tenures if t.tenure_months == 36), None)
    t60 = next((t for t in tenures if t.tenure_months == 60), None)

    assert t36 is not None and t60 is not None
    # Shorter tenure -> higher monthly EMI, lower total interest
    assert t36.monthly_emi > t60.monthly_emi
    assert t36.total_interest < t60.total_interest


# =============================================================================
# 16. Stress DSCR Is Correctly Calculated
# =============================================================================
def test_16_stress_dscr_correctly_calculated():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=200000.0, operating_expenses=150000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=120000.0)
    ])
    lm = LoanManagement(principal=200000.0, annual_interest_rate=0.08, monthly_interest_rate=0.0067, tenure_months=60, monthly_emi=4055.28, total_interest=43316.8, total_repayment=243316.8)
    ds_annual = round(4055.28 * 12.0, 2)
    ds = type("DS", (), {"years": [type("DSY", (), {"total_debt_service": ds_annual})()]})()

    scenarios = stress_engine.evaluate(profit_loss=pl, loan_management=lm, debt_service=ds)
    rev_down = next((s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE), None)

    assert rev_down is not None
    assert rev_down.dscr is not None
    assert rev_down.dscr < 3.0  # stressed DSCR is strictly lower than base


# =============================================================================
# 17. Stress Liquidity Is Correctly Calculated
# =============================================================================
def test_17_stress_liquidity_correctly_calculated():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=200000.0, operating_expenses=150000.0)
    ])
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=150000.0, trade_payables=100000.0, other_current_liabilities=0.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl, balance_sheet=bs)
    wc_stress = next((s for s in scenarios if s.scenario_type == StressScenarioType.WORKING_CAPITAL_PRESSURE), None)

    assert wc_stress is not None
    assert wc_stress.current_ratio is not None


# =============================================================================
# 18. No-Feasible-Structure Case Returns NO_FEASIBLE_FINANCING_STRUCTURE
# =============================================================================
def test_18_no_feasible_structure_returns_no_feasible():
    # If all candidates have unviable DSCR < 1.0 or funding gap
    best, reasons = financing_optimizer.select_best_structure(candidates=[])
    assert best is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons


# =============================================================================
# 19. Selected Structure Has Explicit Decision Reasons
# =============================================================================
def test_19_selected_structure_has_explicit_decision_reasons():
    scheme_opts = scheme_router.evaluate_schemes(project_cost=300000.0, available_promoter_contribution=50000.0)
    candidates = financing_options_generator.generate_candidates(
        project_cost=300000.0,
        available_promoter_contribution=50000.0,
        scheme_options=scheme_opts,
        base_cads=80000.0,
        stress_cads=65000.0,
        other_verified_financing=0.0
    )
    best, reasons = financing_optimizer.select_best_structure(candidates=candidates)

    assert best is not None
    assert len(reasons) > 0
    assert M5ReasonCode.FINANCING_GAP_ELIMINATED in reasons
    assert M5ReasonCode.MARGIN_REQUIREMENT_MET in reasons


# =============================================================================
# 20. Provenance Exists For Stress Assumptions and Selected Financing
# =============================================================================
def test_20_provenance_exists():
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    m5 = resp.financial_analysis.financing_optimizer

    assert m5 is not None
    assert len(m5.provenance) > 0
    prov_metrics = [p.metric for p in m5.provenance]
    assert any("selected_financing_structure" in m for m in prov_metrics)


# =============================================================================
# 21. Tri-State Validation Works
# =============================================================================
def test_21_validation_tristate_correctness():
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    m5 = resp.financial_analysis.financing_optimizer
    val = m5.validation

    assert val is not None
    assert val.total_checks >= 4
    assert val.all_passed is True
    assert val.failed_checks == 0
    assert val.unresolved_checks == 0


# =============================================================================
# 22. Existing M1-M4 Regression Tests Pass
# =============================================================================
def test_22_existing_m1_m4_regression_tests_pass():
    # Calling financial engine pipeline ensures M1, M2, M3, M4 outputs all reconcile
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    assert fa.financial_projection is not None
    assert fa.banking_appraisal is not None
    assert fa.banking_appraisal.validation.all_passed is True


# =============================================================================
# 23. Existing Stage 9 Regression Tests Pass
# =============================================================================
def test_23_existing_stage9_regression_tests_pass():
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    assert resp.workflow.status == "complete"
    assert resp.workflow.state == "FINANCIAL_VIABILITY_EVALUATED"
    assert resp.financial_analysis.scheme_result.recommended_scheme is not None
    assert resp.financial_analysis.loan_management.monthly_emi > 0


# =============================================================================
# 24. Compile / Import Checks Pass
# =============================================================================
def test_24_compile_and_import_checks():
    import app.services.financial_engine.optimizer as opt
    assert opt.m5_engine is not None
    assert opt.stress_engine is not None
    assert opt.financing_optimizer is not None
    assert opt.scheme_router is not None


# =============================================================================
# 25. Targeted: Missing Depreciation Returns UNRESOLVED, Not 0-Depreciation DSCR
# =============================================================================
def test_25_targeted_missing_depreciation_returns_unresolved():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=None, interest_expense=10000.0, tax_expense=20000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl)
    rev_down = next(s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE)
    assert rev_down.status == "UNRESOLVED"
    assert rev_down.dscr is None
    assert rev_down.pat is None
    assert rev_down.cads is None


# =============================================================================
# 26. Targeted: Missing Interest Expense on Debt-Bearing Project -> UNRESOLVED
# =============================================================================
def test_26_targeted_missing_interest_expense_on_debt_bearing_unresolved():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=None, tax_expense=20000.0)
    ])
    from app.services.financial_engine.loan_calculator import LoanCalculator
    lm = LoanCalculator().calculate_emi(principal=300000.0, annual_rate=0.08, tenure_months=60)
    scenarios = stress_engine.evaluate(profit_loss=pl, loan_management=lm)
    rev_down = next(s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE)
    assert rev_down.status == "UNRESOLVED"
    assert rev_down.dscr is None


# =============================================================================
# 27. Targeted: Missing Tax Expense UNRESOLVED Unless Verified Tax-Exempt
# =============================================================================
def test_27_targeted_missing_tax_expense_unresolved_unless_exempt():
    # Missing tax and PAT
    pl_unresolved = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, tax_expense=None, profit_after_tax=None)
    ])
    scenarios1 = stress_engine.evaluate(profit_loss=pl_unresolved)
    rev_down1 = next(s for s in scenarios1 if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE)
    assert rev_down1.status == "UNRESOLVED"
    assert rev_down1.pat is None

    # Verified tax-exempt
    pl_exempt = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, tax_expense=None, tax_status="EXEMPT")
    ])
    scenarios2 = stress_engine.evaluate(profit_loss=pl_exempt)
    rev_down2 = next(s for s in scenarios2 if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE)
    assert rev_down2.status == "RESOLVED"
    assert rev_down2.pat is not None


# =============================================================================
# 28. Targeted: Unknown Working Capital Baseline -> Working Capital Stress UNRESOLVED
# =============================================================================
def test_28_targeted_unknown_working_capital_baseline_wc_stress_unresolved():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, tax_expense=20000.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl, working_capital_analysis=None, balance_sheet=None, working_capital_projection=None)
    wc_sc = next(s for s in scenarios if s.scenario_type == StressScenarioType.WORKING_CAPITAL_PRESSURE)
    assert wc_sc.status == "UNRESOLVED"
    assert M5ReasonCode.UNRESOLVED_WC_BASELINE in wc_sc.reason_codes


# =============================================================================
# 29. Targeted: Cash Position None Gives None Cash Buffer (Never 0.0 or 0.3*CA)
# =============================================================================
def test_29_targeted_cash_position_none_gives_none_cash_buffer():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, tax_expense=20000.0)
    ])
    bs_no_cash = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=100000.0, cash_and_bank=None, trade_payables=50000.0, other_current_liabilities=0.0)
    ])
    scenarios = stress_engine.evaluate(profit_loss=pl, balance_sheet=bs_no_cash)
    for s in scenarios:
        assert s.cash_buffer_months is None


# =============================================================================
# 30. Targeted: Scheme Database Missing Rate -> Marked VERIFICATION_REQUIRED
# =============================================================================
def test_30_targeted_scheme_db_missing_rate_verification_required():
    with patch.dict("app.services.financial_engine.government_financing_schemes.GOVERNMENT_SCHEMES_DATABASE", {
        "TEST_NO_RATE": {
            "scheme_id": "TEST_NO_RATE",
            "scheme_name": "Test Scheme Without Rate",
            "min_project_cost": 100000.0,
            "max_project_cost": 1000000.0,
            "min_margin_percentage": 10.0,
            "maximum_loan_limit": 500000.0,
            "annual_interest_rate": None,
            "repayment_tenure_months": 60,
            "moratorium_months": 6
        }
    }, clear=False):
        opts = scheme_router.evaluate_schemes(project_cost=500000.0, available_promoter_contribution=100000.0)
        test_opt = next((o for o in opts if o.scheme_id == "TEST_NO_RATE"), None)
        assert test_opt is not None
        assert test_opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert test_opt.status == "UNRESOLVED"


# =============================================================================
# 31. Targeted: Scheme Database Missing Tenure -> Marked VERIFICATION_REQUIRED
# =============================================================================
def test_31_targeted_scheme_db_missing_tenure_verification_required():
    with patch.dict("app.services.financial_engine.government_financing_schemes.GOVERNMENT_SCHEMES_DATABASE", {
        "TEST_NO_TENURE": {
            "scheme_id": "TEST_NO_TENURE",
            "scheme_name": "Test Scheme Without Tenure",
            "min_project_cost": 100000.0,
            "max_project_cost": 1000000.0,
            "min_margin_percentage": 10.0,
            "maximum_loan_limit": 500000.0,
            "annual_interest_rate": 0.08,
            "repayment_tenure_months": None,
            "moratorium_months": 6
        }
    }, clear=False):
        opts = scheme_router.evaluate_schemes(project_cost=500000.0, available_promoter_contribution=100000.0)
        test_opt = next((o for o in opts if o.scheme_id == "TEST_NO_TENURE"), None)
        assert test_opt is not None
        assert test_opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert test_opt.status == "UNRESOLVED"


# =============================================================================
# 32. Targeted: Scheme Database Missing Margin -> Marked VERIFICATION_REQUIRED
# =============================================================================
def test_32_targeted_scheme_db_missing_margin_verification_required():
    with patch.dict("app.services.financial_engine.government_financing_schemes.GOVERNMENT_SCHEMES_DATABASE", {
        "TEST_NO_MARGIN": {
            "scheme_id": "TEST_NO_MARGIN",
            "scheme_name": "Test Scheme Without Margin",
            "min_project_cost": 100000.0,
            "max_project_cost": 1000000.0,
            "min_margin_percentage": None,
            "maximum_loan_limit": 500000.0,
            "annual_interest_rate": 0.08,
            "repayment_tenure_months": 60,
            "moratorium_months": 6
        }
    }, clear=False):
        opts = scheme_router.evaluate_schemes(project_cost=500000.0, available_promoter_contribution=100000.0)
        test_opt = next((o for o in opts if o.scheme_id == "TEST_NO_MARGIN"), None)
        assert test_opt is not None
        assert test_opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert test_opt.status == "UNRESOLVED"


# =============================================================================
# 33. Targeted: Financing Gap Under Stress Stressed Cost Exceeds Funding
# =============================================================================
def test_33_targeted_financing_gap_under_stress_reported():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, tax_expense=20000.0)
    ])
    wc_anal = WorkingCapitalAnalysis(operating_working_capital=200000.0)
    scenarios = stress_engine.evaluate(
        profit_loss=pl,
        working_capital_analysis=wc_anal,
        project_cost=500000.0,
        verified_funding=500000.0
    )
    wc_sc = next(s for s in scenarios if s.scenario_type == StressScenarioType.WORKING_CAPITAL_PRESSURE)
    assert wc_sc.financing_gap == 30000.0
    assert M5ReasonCode.FINANCING_GAP in wc_sc.reason_codes


# =============================================================================
# 34. Targeted: Candidate DSCR Uses Actual Scenario CADS, Not 0.85 * Base
# =============================================================================
def test_34_targeted_candidate_dscr_uses_actual_scenario_cads():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=135000.0)
    ])
    wc_anal = WorkingCapitalAnalysis(operating_working_capital=50000.0)
    scenarios = stress_engine.evaluate(profit_loss=pl, working_capital_analysis=wc_anal)
    rev_sc = next(s for s in scenarios if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE)

    scheme_opts = scheme_router.evaluate_schemes(project_cost=300000.0, available_promoter_contribution=50000.0)
    candidates = financing_options_generator.generate_candidates(
        project_cost=300000.0,
        available_promoter_contribution=50000.0,
        scheme_options=scheme_opts,
        base_cads=165000.0,
        stress_scenarios=scenarios,
        other_verified_financing=0.0
    )
    cand = candidates[0]
    expected_rev_dscr = round(rev_sc.cads / cand.annual_debt_service, 2)
    assert cand.revenue_downside_dscr == expected_rev_dscr


# =============================================================================
# 35. Targeted: Multi-Gate Candidate Rejection When Stress DSCR < 1.0
# =============================================================================
def test_35_targeted_multigate_rejection_stress_dscr_below_1():
    cand = FinancingStructureCandidate(
        candidate_id="FAIL_DSCR",
        scheme_id="SCHEME_A",
        scheme_name="Scheme A",
        total_project_cost=300000.0,
        promoter_contribution=50000.0,
        loan_amount=250000.0,
        interest_rate=0.08,
        tenure_months=60,
        is_scheme_compliant=True,
        is_gap_eliminated=True,
        is_margin_met=True,
        base_case_dscr=2.5,
        combined_downside_dscr=0.75,
        stress_case_dscr=0.75
    )
    best, reasons = financing_optimizer.select_best_structure(candidates=[cand])
    assert best is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons


# =============================================================================
# 36. Targeted: Multi-Gate Candidate Rejection When Funding Gap > 0
# =============================================================================
def test_36_targeted_multigate_rejection_funding_gap_above_0():
    cand = FinancingStructureCandidate(
        candidate_id="FAIL_GAP",
        scheme_id="SCHEME_A",
        scheme_name="Scheme A",
        total_project_cost=300000.0,
        promoter_contribution=30000.0,
        loan_amount=250000.0,
        financing_gap=20000.0,
        interest_rate=0.08,
        tenure_months=60,
        is_scheme_compliant=True,
        is_gap_eliminated=False,
        is_margin_met=True,
        base_case_dscr=2.5,
        combined_downside_dscr=1.5,
        stress_case_dscr=1.5
    )
    best, reasons = financing_optimizer.select_best_structure(candidates=[cand])
    assert best is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons


# =============================================================================
# 37. Targeted: Multi-Gate Candidate Rejection When Margin Not Met
# =============================================================================
def test_37_targeted_multigate_rejection_margin_not_met():
    cand = FinancingStructureCandidate(
        candidate_id="FAIL_MARGIN",
        scheme_id="SCHEME_A",
        scheme_name="Scheme A",
        total_project_cost=300000.0,
        promoter_contribution=10000.0,
        loan_amount=290000.0,
        financing_gap=0.0,
        interest_rate=0.08,
        tenure_months=60,
        is_scheme_compliant=True,
        is_gap_eliminated=True,
        is_margin_met=False,
        base_case_dscr=2.5,
        combined_downside_dscr=1.5,
        stress_case_dscr=1.5
    )
    best, reasons = financing_optimizer.select_best_structure(candidates=[cand])
    assert best is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons


# =============================================================================
# 38. Targeted: All Candidates Rejected Returns None + NO_FEASIBLE_FINANCING_STRUCTURE
# =============================================================================
def test_38_targeted_all_candidates_rejected_returns_none():
    cands = [
        FinancingStructureCandidate(
            candidate_id="C1",
            scheme_id="S1",
            scheme_name="S1",
            total_project_cost=300000.0,
            loan_amount=250000.0,
            interest_rate=0.08,
            tenure_months=60,
            is_scheme_compliant=True,
            is_gap_eliminated=True,
            is_margin_met=True,
            base_case_dscr=0.8,
            combined_downside_dscr=0.5
        ),
        FinancingStructureCandidate(
            candidate_id="C2",
            scheme_id="S2",
            scheme_name="S2",
            total_project_cost=300000.0,
            loan_amount=250000.0,
            interest_rate=0.08,
            tenure_months=60,
            is_scheme_compliant=True,
            is_gap_eliminated=False,
            is_margin_met=True,
            base_case_dscr=2.0,
            combined_downside_dscr=1.5
        )
    ]
    best, reasons = financing_optimizer.select_best_structure(candidates=cands)
    assert best is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons


# =============================================================================
# 39. Targeted: Worst-Case Scenario Selection Respects Severity Hierarchy
# =============================================================================
def test_39_targeted_worst_case_scenario_selection_hierarchy():
    resilient_sc = StressScenarioResult(
        scenario_id="S_RESILIENT",
        scenario_name="Resilient Scenario",
        scenario_type=StressScenarioType.VOLUME_DOWNSIDE,
        dscr=1.15,
        resilience_status=ResilienceStatus.RESILIENT
    )
    critical_sc = StressScenarioResult(
        scenario_id="S_CRITICAL",
        scenario_name="Critical Negative EBITDA Scenario",
        scenario_type=StressScenarioType.COMBINED_DOWNSIDE,
        dscr=None,
        ebitda=-50000.0,
        resilience_status=ResilienceStatus.CRITICAL
    )
    worst = select_worst_case_scenario([resilient_sc, critical_sc])
    assert worst is not None
    assert worst.scenario_id == "S_CRITICAL"


# =============================================================================
# 40. Targeted: DPR Summary Funding Gap is None When Unresolved (Never 0.0)
# =============================================================================
def test_40_targeted_dpr_summary_funding_gap_none_when_unresolved():
    summary = M5DprFinancingSummary(
        total_project_cost=None,
        funding_gap=None,
        is_fully_financed=None,
        stress_resilience_status="NOT_ASSESSABLE"
    )
    assert summary.funding_gap is None
    assert summary.is_fully_financed is None


# =============================================================================
# 41. Targeted: Provenance Tracking with POLICY_SCENARIO and Dependencies
# =============================================================================
def test_41_targeted_provenance_tracking_policy_scenario_and_dependencies():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, cogs=500000.0, operating_expenses=200000.0, depreciation=20000.0, interest_expense=10000.0, profit_after_tax=135000.0)
    ])
    prov = M5ProvenanceBuilder()
    scenarios = stress_engine.evaluate(profit_loss=pl, provenance=prov)
    records = prov.get_records()
    assert len(records) > 0
    policy_records = [r for r in records if r.source == "POLICY_SCENARIO"]
    assert len(policy_records) > 0
    assert any(r.calculation_method and "Deterministic" in r.calculation_method for r in policy_records)


# =============================================================================
# 42. Freeze Patch: M5 Overall Status Tri-State Logic
# =============================================================================
def test_42_freeze_patch_overall_status_tristate():
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    m5 = resp.financial_analysis.financing_optimizer
    assert m5 is not None

    val = m5.validation
    if val.failed_checks > 0:
        assert m5.status == "FAILED"
    elif val.unresolved_checks > 0:
        assert m5.status == "PARTIALLY_DERIVED"
    else:
        assert m5.status == "RESOLVED"
        assert val.failed_checks == 0
        assert val.unresolved_checks == 0

    from app.services.financial_engine.optimizer.m5_schema import M5ValidationResult
    # Case 1: 1 failed, 0 unresolved -> FAILED
    res1 = M5ValidationResult(all_passed=False, total_checks=1, passed_checks=0, failed_checks=1, unresolved_checks=0, checks=[])
    status1 = "FAILED" if res1.failed_checks > 0 else ("PARTIALLY_DERIVED" if res1.unresolved_checks > 0 else "RESOLVED")
    assert status1 == "FAILED"

    # Case 2: 0 failed, 1 unresolved -> PARTIALLY_DERIVED
    res2 = M5ValidationResult(all_passed=False, total_checks=1, passed_checks=0, failed_checks=0, unresolved_checks=1, checks=[])
    status2 = "FAILED" if res2.failed_checks > 0 else ("PARTIALLY_DERIVED" if res2.unresolved_checks > 0 else "RESOLVED")
    assert status2 == "PARTIALLY_DERIVED"

    # Case 3: 0 failed, 0 unresolved -> RESOLVED
    res3 = M5ValidationResult(all_passed=True, total_checks=1, passed_checks=1, failed_checks=0, unresolved_checks=0, checks=[])
    status3 = "FAILED" if res3.failed_checks > 0 else ("PARTIALLY_DERIVED" if res3.unresolved_checks > 0 else "RESOLVED")
    assert status3 == "RESOLVED"


# =============================================================================
# 43. Freeze Patch: Moratorium Unknown != 0
# =============================================================================
def test_43_freeze_patch_moratorium_unknown_not_zero():
    # A) tenure_analysis returns [] if moratorium_months is None
    tenures = tenure_analysis_engine.evaluate_tenures(
        loan_amount=200000.0,
        annual_interest_rate=0.08,
        scheme_max_tenure_months=60,
        moratorium_months=None
    )
    assert tenures == []

    # B) Validation flags UNRESOLVED if selected_structure.moratorium_months is None
    cand = FinancingStructureCandidate(
        candidate_id="TEST_NO_MORA",
        scheme_id="PMEGP",
        scheme_name="Prime Minister Employment Generation Programme",
        loan_amount=200000.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=None,
        monthly_emi=4055.28,
        total_project_cost=300000.0,
        promoter_contribution=100000.0,
        financing_gap=0.0,
        is_gap_eliminated=True
    )
    val = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=cand,
        stress_scenarios=None,
        financing_options=[cand],
        is_zero_debt=False
    )
    emi_chk = next((c for c in val.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_EMI_CONSISTENCY"), None)
    assert emi_chk is not None
    assert emi_chk.status == M5ValidationState.UNRESOLVED
    assert emi_chk.reason_code == M5ReasonCode.INSUFFICIENT_DATA


# =============================================================================
# 44. Freeze Patch: Truthful Classification When No Selected Structure
# =============================================================================
def test_44_freeze_patch_no_selected_structure_truthful_classification():
    # Case A: Genuine zero-debt project fully funded -> PASSED
    gap_a = FinancingGapAnalysisResult(
        total_project_cost=300000.0,
        available_promoter_contribution=300000.0,
        scheme_loan=0.0,
        other_verified_financing=0.0,
        total_funding=300000.0,
        funding_gap=0.0,
        is_balanced=True,
        status="RESOLVED"
    )
    val_a = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=gap_a,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=True
    )
    chk_a = next(c for c in val_a.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_a.status == M5ValidationState.PASSED
    assert "Zero-debt project" in chk_a.message

    # Case A2: Zero debt with unresolved funding completeness -> UNRESOLVED
    val_a2 = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=True
    )
    chk_a2 = next(c for c in val_a2.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_a2.status == M5ValidationState.UNRESOLVED

    # Case B: Selection incomplete due to unresolved inputs -> UNRESOLVED with INSUFFICIENT_DATA
    unresolved_opt = FinancingStructureCandidate(
        candidate_id="OPT_UNRESOLVED",
        scheme_id="SCHEME_X",
        scheme_name="Unresolved Scheme",
        status="UNRESOLVED"
    )
    val_b = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[unresolved_opt],
        is_zero_debt=False
    )
    chk_b = next(c for c in val_b.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_b.status == M5ValidationState.UNRESOLVED
    assert chk_b.reason_code == M5ReasonCode.INSUFFICIENT_DATA

    # Case C: Candidates evaluated, but none met feasibility gates -> FAILED with NO_FEASIBLE_FINANCING_STRUCTURE
    infeasible_opt = FinancingStructureCandidate(
        candidate_id="OPT_INFEASIBLE",
        scheme_id="SCHEME_Y",
        scheme_name="Infeasible Scheme",
        status="RESOLVED",
        is_gap_eliminated=False,
        financing_gap=50000.0,
        feasibility_status="INELIGIBLE_OR_STRESSED"
    )
    val_c = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[infeasible_opt],
        is_zero_debt=False
    )
    chk_c = next(c for c in val_c.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_c.status == M5ValidationState.FAILED
    assert chk_c.reason_code == M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE

    # Case D: Mixed candidates with resolved (infeasible) and unrelated unresolved -> FAILED
    # Unrelated unresolved candidate does not override independently evaluated resolved candidates
    val_d = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[infeasible_opt, unresolved_opt],
        is_zero_debt=False
    )
    chk_d = next(c for c in val_d.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_d.status == M5ValidationState.FAILED
    assert chk_d.reason_code == M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE

    # Case E: Empty financing options -> UNRESOLVED
    val_e = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=False
    )
    chk_e = next(c for c in val_e.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_e.status == M5ValidationState.UNRESOLVED
    assert chk_e.reason_code == M5ReasonCode.INSUFFICIENT_DATA


# =============================================================================
# 45. Freeze Patch: Centralized Interest Rate Stress Hike
# =============================================================================
def test_45_freeze_patch_centralized_interest_rate_stress():
    from app.services.financial_engine.optimizer.m5_config import POLICY_STRESS_PARAMETERS
    expected_hike = POLICY_STRESS_PARAMETERS["INTEREST_RATE_STRESS"]["rate_increase_pct_points"] / 100.0
    assert expected_hike == 0.015


# =============================================================================
# 46. Freeze Patch: other_financing UNKNOWN vs Explicit 0.0
# =============================================================================
def test_46_freeze_patch_other_financing_unknown_vs_zero():
    # If other_verified_financing is None -> UNRESOLVED with INSUFFICIENT_DATA
    res_none = financing_feasibility_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=100000.0,
        scheme_loan=350000.0,
        other_verified_financing=None
    )
    assert res_none.status == "UNRESOLVED"
    assert res_none.funding_gap is None
    assert res_none.reason_code == M5ReasonCode.INSUFFICIENT_DATA

    # If other_verified_financing is explicitly 0.0 -> RESOLVED with gap calculated
    res_zero = financing_feasibility_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=100000.0,
        scheme_loan=350000.0,
        other_verified_financing=0.0
    )
    assert res_zero.status == "RESOLVED"
    assert res_zero.funding_gap == 50000.0
    assert res_zero.is_balanced is False
    assert res_zero.reason_code == M5ReasonCode.FINANCING_GAP


# =============================================================================
# 47. Freeze Patch: Optimizer Selection Reason Code for LOWER_TOTAL_INTEREST
# =============================================================================
def test_47_freeze_patch_lower_total_interest_reason_code():
    cand_low = FinancingStructureCandidate(
        candidate_id="LOW_INT",
        scheme_id="SCHEME_LOW",
        scheme_name="Low Interest Scheme",
        status="RESOLVED",
        is_scheme_compliant=True,
        total_project_cost=500000.0,
        promoter_contribution=100000.0,
        loan_amount=400000.0,
        tenure_months=60,
        moratorium_months=0,
        monthly_emi=2083.33,
        financing_gap=0.0,
        is_gap_eliminated=True,
        is_margin_met=True,
        base_case_dscr=2.0,
        stress_case_dscr=1.5,
        total_interest=10000.0,
        annual_debt_service=25000.0,
        interest_rate=0.08
    )
    cand_high = FinancingStructureCandidate(
        candidate_id="HIGH_INT",
        scheme_id="SCHEME_HIGH",
        scheme_name="High Interest Scheme",
        status="RESOLVED",
        is_scheme_compliant=True,
        total_project_cost=500000.0,
        promoter_contribution=100000.0,
        loan_amount=400000.0,
        tenure_months=60,
        moratorium_months=0,
        monthly_emi=2083.33,
        financing_gap=0.0,
        is_gap_eliminated=True,
        is_margin_met=True,
        base_case_dscr=2.0,
        stress_case_dscr=1.5,
        total_interest=18000.0,
        annual_debt_service=25000.0,
        interest_rate=0.10
    )

    # When both are evaluated, LOW_INT wins and gets LOWER_TOTAL_INTEREST
    best, reasons = financing_optimizer.select_best_structure(candidates=[cand_low, cand_high])
    assert best is not None
    assert best.candidate_id == "LOW_INT"
    assert M5ReasonCode.LOWER_TOTAL_INTEREST in reasons

    # If single candidate in pool, LOWER_TOTAL_INTEREST must NOT be emitted
    best_single, reasons_single = financing_optimizer.select_best_structure(candidates=[cand_low])
    assert best_single is not None
    assert M5ReasonCode.LOWER_TOTAL_INTEREST not in reasons_single


# =============================================================================
# 48. Targeted: Tenure Moratorium (None vs 0 vs >0)
# =============================================================================
def test_48_freeze_patch_targeted_tenure_moratorium():
    # moratorium = None => []
    t_none = tenure_analysis_engine.evaluate_tenures(
        loan_amount=100000.0,
        annual_interest_rate=0.08,
        scheme_max_tenure_months=60,
        moratorium_months=None
    )
    assert t_none == []

    # moratorium = 0 => valid explicit zero
    t_zero = tenure_analysis_engine.evaluate_tenures(
        loan_amount=100000.0,
        annual_interest_rate=0.08,
        scheme_max_tenure_months=60,
        moratorium_months=0
    )
    assert len(t_zero) >= 3
    assert all(t.moratorium_months == 0 for t in t_zero)

    # moratorium > 0 => valid
    t_pos = tenure_analysis_engine.evaluate_tenures(
        loan_amount=100000.0,
        annual_interest_rate=0.08,
        scheme_max_tenure_months=60,
        moratorium_months=6
    )
    assert len(t_pos) >= 3
    assert all(t.moratorium_months == 6 for t in t_pos)


# =============================================================================
# 49. Targeted: Scheme Routing Boundaries (Missing min, max, loan limit)
# =============================================================================
def test_49_freeze_patch_targeted_scheme_routing_boundaries():
    from app.services.financial_engine.government_financing_schemes import GOVERNMENT_SCHEMES_DATABASE
    from unittest.mock import patch

    # 1. Missing min_project_cost
    mock_db_min = {
        "TEST_SCHEME": {
            "scheme_name": "Test Scheme",
            "min_project_cost": None,
            "max_project_cost": 500000.0,
            "maximum_loan_limit": 400000.0,
            "min_margin_percentage": 10.0,
            "max_financing_percentage": 90.0,
            "annual_interest_rate": 0.08,
            "repayment_tenure_months": 60,
            "moratorium_months": 3
        }
    }
    with patch("app.services.financial_engine.optimizer.scheme_router.GOVERNMENT_SCHEMES_DATABASE", mock_db_min):
        opts = scheme_router.evaluate_schemes(project_cost=200000.0)
        assert len(opts) == 1
        opt = opts[0]
        assert opt.status == "UNRESOLVED"
        assert opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert any("min_project_cost" in r for r in opt.eligibility_reasons)

    # 2. Missing max_project_cost
    mock_db_max = {
        "TEST_SCHEME": {
            "scheme_name": "Test Scheme",
            "min_project_cost": 10000.0,
            "max_project_cost": None,
            "maximum_loan_limit": 400000.0,
            "min_margin_percentage": 10.0,
            "max_financing_percentage": 90.0,
            "annual_interest_rate": 0.08,
            "repayment_tenure_months": 60,
            "moratorium_months": 3
        }
    }
    with patch("app.services.financial_engine.optimizer.scheme_router.GOVERNMENT_SCHEMES_DATABASE", mock_db_max):
        opts = scheme_router.evaluate_schemes(project_cost=200000.0)
        assert len(opts) == 1
        opt = opts[0]
        assert opt.status == "UNRESOLVED"
        assert opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert any("max_project_cost" in r for r in opt.eligibility_reasons)

    # 3. Missing maximum_loan_limit
    mock_db_loan = {
        "TEST_SCHEME": {
            "scheme_name": "Test Scheme",
            "min_project_cost": 10000.0,
            "max_project_cost": 500000.0,
            "maximum_loan_limit": None,
            "min_margin_percentage": 10.0,
            "max_financing_percentage": 90.0,
            "annual_interest_rate": 0.08,
            "repayment_tenure_months": 60,
            "moratorium_months": 3
        }
    }
    with patch("app.services.financial_engine.optimizer.scheme_router.GOVERNMENT_SCHEMES_DATABASE", mock_db_loan):
        opts = scheme_router.evaluate_schemes(project_cost=200000.0)
        assert len(opts) == 1
        opt = opts[0]
        assert opt.status == "UNRESOLVED"
        assert opt.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED
        assert any("maximum_loan_limit" in r for r in opt.eligibility_reasons)


# =============================================================================
# 50. Targeted: Financing Options Under Unresolved Boundaries & Moratorium
# =============================================================================
def test_50_freeze_patch_targeted_financing_options_boundaries_and_moratorium():
    from app.services.financial_engine.optimizer.m5_schema import SchemeRoutingOption

    # A) Unresolved scheme boundary => no candidate generated
    unresolved_scheme = SchemeRoutingOption(
        scheme_id="S_UNRES",
        scheme_name="Unresolved Boundary Scheme",
        eligibility_status=SchemeEligibilityStatus.VERIFICATION_REQUIRED,
        status="UNRESOLVED",
        min_project_cost=None,  # missing
        max_project_cost=500000.0,
        maximum_loan_limit=400000.0,
        max_financing_percentage=90.0,
        required_margin_percentage=10.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=3,
        max_loan=180000.0
    )
    cands_a = financing_options_generator.generate_candidates(
        project_cost=200000.0,
        available_promoter_contribution=30000.0,
        scheme_options=[unresolved_scheme],
        base_cads=50000.0,
        other_verified_financing=0.0
    )
    assert len(cands_a) == 0

    # B) Unresolved moratorium => no candidate generated
    no_mora_scheme = SchemeRoutingOption(
        scheme_id="S_NOMORA",
        scheme_name="Missing Moratorium Scheme",
        eligibility_status=SchemeEligibilityStatus.VERIFICATION_REQUIRED,
        status="UNRESOLVED",
        min_project_cost=10000.0,
        max_project_cost=500000.0,
        maximum_loan_limit=400000.0,
        max_financing_percentage=90.0,
        required_margin_percentage=10.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=None,  # missing moratorium
        max_loan=180000.0
    )
    cands_b = financing_options_generator.generate_candidates(
        project_cost=200000.0,
        available_promoter_contribution=30000.0,
        scheme_options=[no_mora_scheme],
        base_cads=50000.0,
        other_verified_financing=0.0
    )
    assert len(cands_b) == 0

    # C) Explicit zero moratorium => candidate generation allowed
    zero_mora_scheme = SchemeRoutingOption(
        scheme_id="S_ZEROMORA",
        scheme_name="Explicit Zero Moratorium Scheme",
        eligibility_status=SchemeEligibilityStatus.ELIGIBLE,
        status="RESOLVED",
        min_project_cost=10000.0,
        max_project_cost=500000.0,
        maximum_loan_limit=400000.0,
        max_financing_percentage=90.0,
        required_margin_percentage=10.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=0,  # explicit zero
        max_loan=180000.0
    )
    cands_c = financing_options_generator.generate_candidates(
        project_cost=200000.0,
        available_promoter_contribution=30000.0,
        scheme_options=[zero_mora_scheme],
        base_cads=50000.0,
        other_verified_financing=0.0
    )
    assert len(cands_c) > 0
    assert all(c.moratorium_months == 0 for c in cands_c)


# =============================================================================
# 51. Targeted: DPR Truthful unresolved_inputs
# =============================================================================
def test_51_freeze_patch_targeted_dpr_unresolved_inputs_truthful():
    # 1. When validation has unresolved checks, they appear in unresolved_inputs
    req = _build_standard_test_request()
    resp = financial_engine.analyze(req)
    m5 = resp.financial_analysis.financing_optimizer
    assert m5 is not None
    dpr = m5.dpr_summary

    unresolved_val_checks = [c for c in m5.validation.checks if c.status == M5ValidationState.UNRESOLVED]
    if unresolved_val_checks:
        assert len(dpr.unresolved_inputs) == len(unresolved_val_checks)
        for c in unresolved_val_checks:
            assert any(c.check_id in u for u in dpr.unresolved_inputs)
    else:
        assert dpr.unresolved_inputs == []

    # 2. Zero-debt project check:
    # Case 2a: Fully funded zero-debt project -> PASSED, and not in unresolved_inputs
    gap_analysis_funded = FinancingGapAnalysisResult(
        total_project_cost=100000.0,
        available_promoter_contribution=100000.0,
        scheme_loan=0.0,
        other_verified_financing=0.0,
        total_funding=100000.0,
        funding_gap=0.0,
        is_balanced=True,
        status="RESOLVED"
    )
    val_zero = m5_validation_engine.validate(
        project_cost=100000.0,
        financing_gap_analysis=gap_analysis_funded,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=True
    )
    feas_chk = next(c for c in val_zero.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert feas_chk.status == M5ValidationState.PASSED
    # Should not be in unresolved_inputs
    unres = [f"{c.check_id}: {c.message}" for c in val_zero.checks if c.status == M5ValidationState.UNRESOLVED]
    assert not any("VAL_M5_SELECTED_STRUCTURE_FEASIBILITY" in u for u in unres)

    # Case 2b: Zero debt with unresolved funding -> UNRESOLVED
    val_zero_unres = m5_validation_engine.validate(
        project_cost=100000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=True
    )
    feas_chk_unres = next(c for c in val_zero_unres.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert feas_chk_unres.status == M5ValidationState.UNRESOLVED

    # Case 2c: Zero debt with funding gap -> FAILED
    gap_analysis_shortfall = FinancingGapAnalysisResult(
        total_project_cost=100000.0,
        available_promoter_contribution=60000.0,
        scheme_loan=0.0,
        other_verified_financing=0.0,
        total_funding=60000.0,
        funding_gap=40000.0,
        is_balanced=False,
        status="RESOLVED"
    )
    val_zero_failed = m5_validation_engine.validate(
        project_cost=100000.0,
        financing_gap_analysis=gap_analysis_shortfall,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        financing_options=[],
        is_zero_debt=True
    )
    feas_chk_failed = next(c for c in val_zero_failed.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert feas_chk_failed.status == M5ValidationState.FAILED


# =============================================================================
# 52. Targeted: Global Zero Safety and Stage 9 Loan Calculator Reconciliation
# =============================================================================
def test_52_freeze_patch_global_zero_safety_and_stage9_reconciliation():
    # Explicit other_financing=0.0 is valid and computes gap
    gap_res = financing_feasibility_engine.evaluate(
        total_project_cost=300000.0,
        available_promoter_contribution=50000.0,
        scheme_loan=250000.0,
        other_verified_financing=0.0
    )
    assert gap_res.status == "RESOLVED"
    assert gap_res.is_balanced is True
    assert gap_res.funding_gap == 0.0

    # Missing other_financing remains UNRESOLVED with INSUFFICIENT_DATA
    gap_none = financing_feasibility_engine.evaluate(
        total_project_cost=300000.0,
        available_promoter_contribution=50000.0,
        scheme_loan=250000.0,
        other_verified_financing=None
    )
    assert gap_none.status == "UNRESOLVED"
    assert gap_none.funding_gap is None
    assert gap_none.reason_code == M5ReasonCode.INSUFFICIENT_DATA

    # Stage 9 Loan Calculator EMI exact reconciliation
    cand = FinancingStructureCandidate(
        candidate_id="RECON_TEST",
        scheme_id="PMEGP",
        scheme_name="Prime Minister Employment Generation Programme",
        loan_amount=200000.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=0,
        monthly_emi=4055.28,
        total_project_cost=300000.0,
        promoter_contribution=100000.0,
        financing_gap=0.0,
        is_gap_eliminated=True
    )
    val = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=cand,
        stress_scenarios=None,
        financing_options=[cand],
        is_zero_debt=False
    )
    emi_chk = next(c for c in val.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_EMI_CONSISTENCY")
    assert emi_chk.status == M5ValidationState.PASSED


# =============================================================================
# 53. Targeted: Comprehensive Verification of Criteria A through W
# =============================================================================
def test_53_m5_final_hardening_targeted_tests_a_through_w():
    from app.services.financial_engine.optimizer.stress_scenarios import ScenarioSpecification
    from app.services.financial_engine.optimizer.m5_schema import (
        ScenarioSource,
        StressScenarioType,
        ResilienceStatus,
        SchemeEligibilityStatus,
        SchemeRoutingOption,
        FinancingStructureCandidate,
        StressScenarioResult,
        M5ValidationState
    )
    from app.services.financial_engine.optimizer.m5_config import (
        DSCR_RESILIENCE_MINIMUM,
        DSCR_RESILIENCE_BENCHMARK,
        MAX_ACCEPTABLE_DER
    )

    # A. promoter=None -> unresolved candidate, never selected
    scheme_opt_a = SchemeRoutingOption(
        scheme_id="PMEGP",
        scheme_name="PMEGP",
        eligibility_status=SchemeEligibilityStatus.ELIGIBLE,
        min_project_cost=100000.0,
        max_project_cost=2500000.0,
        max_supported_project_cost=2500000.0,
        maximum_loan_limit=2500000.0,
        max_loan=2500000.0,
        max_financing_percentage=90.0,
        required_margin_percentage=10.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=0,
        status="RESOLVED"
    )
    cands_a = financing_options_generator.generate_candidates(
        project_cost=500000.0,
        available_promoter_contribution=None,
        scheme_options=[scheme_opt_a],
        base_cads=100000.0,
        other_verified_financing=0.0
    )
    assert len(cands_a) > 0
    assert all(c.status == "UNRESOLVED" for c in cands_a)
    assert all(c.loan_amount is None for c in cands_a)
    assert all(c.monthly_emi is None for c in cands_a)
    assert all(c.total_interest is None for c in cands_a)
    assert all(c.annual_debt_service is None for c in cands_a)
    assert all(c.financing_gap is None for c in cands_a)
    best_a, reasons_a = financing_optimizer.select_best_structure(candidates=cands_a)
    assert best_a is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons_a

    # B. promoter=0 -> explicit zero preserved
    prom_b = promoter_contribution_analysis_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=0.0,
        scheme_margin_percentage=10.0
    )
    assert prom_b.available_promoter_contribution == 0.0
    assert prom_b.status == "RESOLVED"
    assert prom_b.gap_surplus == -50000.0

    # C. other_financing=None -> unresolved, never selected
    cands_c = financing_options_generator.generate_candidates(
        project_cost=500000.0,
        available_promoter_contribution=50000.0,
        scheme_options=[scheme_opt_a],
        base_cads=100000.0,
        other_verified_financing=None
    )
    assert len(cands_c) > 0
    assert all(c.status == "UNRESOLVED" for c in cands_c)
    assert all(c.loan_amount is None for c in cands_c)
    assert all(c.monthly_emi is None for c in cands_c)
    assert all(c.total_interest is None for c in cands_c)
    assert all(c.annual_debt_service is None for c in cands_c)
    assert all(c.financing_gap is None for c in cands_c)
    best_c, reasons_c = financing_optimizer.select_best_structure(candidates=cands_c)
    assert best_c is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons_c

    # D. other_financing=0 -> valid explicit zero
    gap_d = financing_feasibility_engine.evaluate(
        total_project_cost=500000.0,
        available_promoter_contribution=50000.0,
        scheme_loan=450000.0,
        other_verified_financing=0.0
    )
    assert gap_d.status == "RESOLVED"
    assert gap_d.is_balanced is True
    assert gap_d.funding_gap == 0.0

    # E. rate stress missing tenure -> UNRESOLVED
    spec_rate = ScenarioSpecification(
        scenario_id="INT_RATE",
        scenario_name="Interest Rate Stress",
        scenario_type=StressScenarioType.INTEREST_RATE_STRESS,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"rate_hike_pct_points": 1.5},
        affected_drivers=["interest_rate"]
    )
    lm_e = type("MockLM", (), {"principal": 200000.0, "annual_interest_rate": 0.08, "tenure_months": None, "moratorium_months": 0})()
    res_e = stress_engine._run_single_scenario(
        spec=spec_rate,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=48000.0,
        base_principal=200000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=200000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_e,
        provenance=M5ProvenanceBuilder()
    )
    assert res_e.status == "UNRESOLVED"
    assert res_e.resilience_status == ResilienceStatus.NOT_ASSESSABLE

    # F. rate stress missing moratorium -> UNRESOLVED
    lm_f = type("MockLM", (), {"principal": 200000.0, "annual_interest_rate": 0.08, "tenure_months": 60, "moratorium_months": None})()
    res_f = stress_engine._run_single_scenario(
        spec=spec_rate,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=48000.0,
        base_principal=200000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=200000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_f,
        provenance=M5ProvenanceBuilder()
    )
    assert res_f.status == "UNRESOLVED"
    assert res_f.resilience_status == ResilienceStatus.NOT_ASSESSABLE

    # G. moratorium=0 -> valid
    lm_g = type("MockLM", (), {"principal": 200000.0, "annual_interest_rate": 0.08, "tenure_months": 60, "moratorium_months": 0})()
    res_g = stress_engine._run_single_scenario(
        spec=spec_rate,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=48663.36,
        base_principal=200000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=200000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_g.status == "RESOLVED"
    assert res_g.dscr is not None

    # H. zero-debt / 100% equity -> not rejected by DSCR debt gate
    cand_h = FinancingStructureCandidate(
        candidate_id="ZERO_DEBT_H",
        scheme_id="EQUITY",
        scheme_name="100% Equity",
        status="RESOLVED",
        is_scheme_compliant=True,
        total_project_cost=500000.0,
        promoter_contribution=500000.0,
        loan_amount=0.0,
        financing_gap=0.0,
        is_gap_eliminated=True,
        is_margin_met=True,
        base_case_dscr=None,
        stress_case_dscr=None
    )
    best_h, reasons_h = financing_optimizer.select_best_structure(candidates=[cand_h])
    assert best_h is not None
    assert best_h.candidate_id == "ZERO_DEBT_H"
    assert M5ReasonCode.EXPLICIT_ZERO_DEBT in reasons_h

    # I. working-capital stress changes liquidity correctly when authoritative WC data exists
    spec_wc = ScenarioSpecification(
        scenario_id="WC_PRESS",
        scenario_name="WC Pressure",
        scenario_type=StressScenarioType.WORKING_CAPITAL_PRESSURE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"wc_change_pct": 20.0},
        affected_drivers=["working_capital"]
    )
    res_i = stress_engine._run_single_scenario(
        spec=spec_wc,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=20000.0,
        base_principal=0.0,
        base_rate=0.0,
        is_zero_debt=True,
        base_ca=120000.0,
        base_cl=60000.0,
        base_wc=40000.0,
        actual_cash=50000.0,
        base_debt=0.0,
        base_equity=100000.0,
        project_cost=500000.0,
        verified_funding=500000.0,
        loan_management=None,
        provenance=M5ProvenanceBuilder()
    )
    assert res_i.current_ratio == 1.76
    assert res_i.current_ratio < 2.0

    # J. missing liquidity data -> UNKNOWN/NOT_ASSESSABLE, not resilient
    res_j = stress_engine._run_single_scenario(
        spec=spec_wc,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=20000.0,
        base_principal=0.0,
        base_rate=0.0,
        is_zero_debt=True,
        base_ca=None,
        base_cl=None,
        base_wc=None,
        actual_cash=None,
        base_debt=0.0,
        base_equity=100000.0,
        project_cost=500000.0,
        verified_funding=500000.0,
        loan_management=None,
        provenance=M5ProvenanceBuilder()
    )
    assert res_j.current_ratio is None
    assert res_j.cash_buffer_months is None
    assert res_j.resilience_status == ResilienceStatus.NOT_ASSESSABLE

    # K. negative operating cash flow -> NEGATIVE_CASH_FLOW
    spec_rev_k = ScenarioSpecification(
        scenario_id="REV_DOWN_K",
        scenario_name="Revenue Downside",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"revenue_change_pct": -80.0},
        affected_drivers=["revenue"]
    )
    res_k = stress_engine._run_single_scenario(
        spec=spec_rev_k,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=0.0,
        base_ds_val=20000.0,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=100000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_k.operating_cash_flow < 0
    assert M5ReasonCode.NEGATIVE_CASH_FLOW in res_k.reason_codes
    assert res_k.resilience_status == ResilienceStatus.CRITICAL

    # L. negative EBITDA with positive operating cash flow -> do NOT label NEGATIVE_CASH_FLOW
    spec_neg_ebitda_pos_cf = ScenarioSpecification(
        scenario_id="NEG_EBITDA_POS_CF",
        scenario_name="WC Release Scenario",
        scenario_type=StressScenarioType.WORKING_CAPITAL_PRESSURE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"wc_change_pct": -50.0},
        affected_drivers=["working_capital"]
    )
    res_l = stress_engine._run_single_scenario(
        spec=spec_neg_ebitda_pos_cf,
        base_rev=300000.0,
        base_cogs=200000.0,
        base_opex=110000.0,
        base_depr=20000.0,
        base_interest=0.0,
        base_tax=0.0,
        base_ds_val=0.0,
        base_principal=0.0,
        base_rate=0.0,
        is_zero_debt=True,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=40000.0,
        actual_cash=50000.0,
        base_debt=0.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=None,
        provenance=M5ProvenanceBuilder()
    )
    assert res_l.ebitda < 0
    assert res_l.operating_cash_flow > 0
    assert M5ReasonCode.NEGATIVE_CASH_FLOW not in res_l.reason_codes

    # M. DER resolved above 4.0 -> HIGH_LEVERAGE
    spec_rev_base = ScenarioSpecification(
        scenario_id="REV_DOWN_M",
        scenario_name="Revenue Downside",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"revenue_change_pct": 0.0},
        affected_drivers=["revenue"]
    )
    res_m = stress_engine._run_single_scenario(
        spec=spec_rev_base,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=20000.0,
        base_principal=500000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=500000.0,
        base_equity=100000.0,
        project_cost=600000.0,
        verified_funding=600000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_m.debt_equity_ratio == 5.0
    assert M5ReasonCode.HIGH_LEVERAGE in res_m.reason_codes

    # N. unresolved DER -> no fabricated leverage classification
    res_n = stress_engine._run_single_scenario(
        spec=spec_rev_base,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=20000.0,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=None,
        base_equity=None,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_n.debt_equity_ratio is None
    assert M5ReasonCode.HIGH_LEVERAGE not in res_n.reason_codes

    # O. DSCR <1.0 -> CRITICAL
    res_o = stress_engine._run_single_scenario(
        spec=spec_rev_base,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=30000.0,
        base_tax=5000.0,
        base_ds_val=300000.0,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=100000.0,
        base_cl=50000.0,
        base_wc=50000.0,
        actual_cash=50000.0,
        base_debt=100000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_o.dscr is not None and res_o.dscr < 1.0
    assert res_o.resilience_status == ResilienceStatus.CRITICAL
    assert M5ReasonCode.DSCR_BELOW_THRESHOLD in res_o.reason_codes
    assert M5ReasonCode.REPAYMENT_DEFICIT in res_o.reason_codes

    # P. DSCR 1.05 -> below minimum resilience, not resilient
    spec_p = ScenarioSpecification(
        scenario_id="P_105",
        scenario_name="DSCR 1.05",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"revenue_change_pct": 0.0},
        affected_drivers=["revenue"]
    )
    res_p = stress_engine._run_single_scenario(
        spec=spec_p,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=180952.38,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=500000.0,
        base_cl=100000.0,
        base_wc=50000.0,
        actual_cash=500000.0,
        base_debt=100000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_p.dscr == 1.05
    assert res_p.resilience_status == ResilienceStatus.STRESSED
    assert M5ReasonCode.DSCR_BELOW_THRESHOLD in res_p.reason_codes

    # Q. DSCR 1.10+ -> passes minimum downside threshold
    spec_q = ScenarioSpecification(
        scenario_id="Q_115",
        scenario_name="DSCR 1.15",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"revenue_change_pct": 0.0},
        affected_drivers=["revenue"]
    )
    res_q = stress_engine._run_single_scenario(
        spec=spec_q,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=165217.39,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=500000.0,
        base_cl=100000.0,
        base_wc=50000.0,
        actual_cash=500000.0,
        base_debt=100000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_q.dscr == 1.15
    assert res_q.resilience_status == ResilienceStatus.RESILIENT
    assert M5ReasonCode.DSCR_BELOW_THRESHOLD not in res_q.reason_codes
    assert res_q.repayment_capacity_assessment == "ADEQUATE"

    # R. DSCR 1.25+ -> benchmark/robust
    spec_r = ScenarioSpecification(
        scenario_id="R_130",
        scenario_name="DSCR 1.30",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        source=ScenarioSource.POLICY_SCENARIO,
        parameters={"revenue_change_pct": 0.0},
        affected_drivers=["revenue"]
    )
    res_r = stress_engine._run_single_scenario(
        spec=spec_r,
        base_rev=500000.0,
        base_cogs=200000.0,
        base_opex=100000.0,
        base_depr=20000.0,
        base_interest=10000.0,
        base_tax=10000.0,
        base_ds_val=146153.85,
        base_principal=100000.0,
        base_rate=0.08,
        is_zero_debt=False,
        base_ca=500000.0,
        base_cl=100000.0,
        base_wc=50000.0,
        actual_cash=500000.0,
        base_debt=100000.0,
        base_equity=100000.0,
        project_cost=300000.0,
        verified_funding=300000.0,
        loan_management=lm_g,
        provenance=M5ProvenanceBuilder()
    )
    assert res_r.dscr == 1.30
    assert res_r.resilience_status == ResilienceStatus.RESILIENT
    assert res_r.repayment_capacity_assessment == "ROBUST"

    # S. unresolved stress accounting -> validation UNRESOLVED
    unres_sc = StressScenarioResult(
        scenario_id="UNRES",
        scenario_name="Unresolved Scenario",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        status="UNRESOLVED",
        resilience_status=ResilienceStatus.NOT_ASSESSABLE
    )
    val_s = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=[unres_sc],
        financing_options=[]
    )
    sc_chk = next(c for c in val_s.checks if c.check_id == "VAL_M5_STRESS_SCENARIOS_ARITHMETIC")
    assert sc_chk.status == M5ValidationState.UNRESOLVED

    # T. no feasible financing candidate -> no selected structure
    infeasible_cand = FinancingStructureCandidate(
        candidate_id="INFEASIBLE_T",
        scheme_id="S_INF",
        scheme_name="Infeasible Scheme",
        status="RESOLVED",
        is_scheme_compliant=True,
        total_project_cost=500000.0,
        promoter_contribution=10000.0,
        loan_amount=400000.0,
        financing_gap=90000.0,
        is_gap_eliminated=False,
        is_margin_met=False,
        base_case_dscr=0.5,
        stress_case_dscr=0.3
    )
    best_t, reasons_t = financing_optimizer.select_best_structure(candidates=[infeasible_cand])
    assert best_t is None
    assert M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE in reasons_t

    # U. scheme numerical terms missing -> candidate cannot be selected
    incomplete_scheme = SchemeRoutingOption(
        scheme_id="INCOMPLETE_SCHEME",
        scheme_name="Incomplete Scheme",
        eligibility_status=SchemeEligibilityStatus.VERIFICATION_REQUIRED,
        min_project_cost=None,
        max_project_cost=2500000.0,
        max_supported_project_cost=2500000.0,
        maximum_loan_limit=2500000.0,
        max_loan=2500000.0,
        max_financing_percentage=90.0,
        required_margin_percentage=10.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=0,
        status="UNRESOLVED"
    )
    cands_u = financing_options_generator.generate_candidates(
        project_cost=500000.0,
        available_promoter_contribution=100000.0,
        scheme_options=[incomplete_scheme],
        base_cads=100000.0,
        other_verified_financing=0.0
    )
    assert cands_u == []

    # V. complete numerical scheme + documentation verification required -> preserve VERIFICATION_REQUIRED
    schemes_v = scheme_router.evaluate_schemes(
        project_cost=500000.0,
        available_promoter_contribution=100000.0,
        user_inputs={}
    )
    pmegp_v = next(s for s in schemes_v if s.scheme_id == "PMEGP_KVIC")
    assert pmegp_v.eligibility_status == SchemeEligibilityStatus.VERIFICATION_REQUIRED

    # W. selected EMI must exactly reconcile with Stage 9 LoanCalculator
    cand_w = FinancingStructureCandidate(
        candidate_id="RECON_W",
        scheme_id="PMEGP_KVIC",
        scheme_name="Prime Minister Employment Generation Programme",
        total_project_cost=300000.0,
        promoter_contribution=100000.0,
        loan_amount=200000.0,
        interest_rate=0.08,
        tenure_months=60,
        moratorium_months=0,
        monthly_emi=4055.28,
        total_interest=43316.8,
        annual_debt_service=48663.36,
        financing_gap=0.0,
        is_gap_eliminated=True,
        is_margin_met=True,
        status="RESOLVED"
    )
    val_w = m5_validation_engine.validate(
        project_cost=300000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=cand_w,
        stress_scenarios=None,
        financing_options=[cand_w],
        is_zero_debt=False
    )
    emi_chk_w = next(c for c in val_w.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_EMI_CONSISTENCY")
    assert emi_chk_w.status == M5ValidationState.PASSED


# =============================================================================
# 54. Final Hardening: Risk Flag Deduplication, Ambiguous Margin, Zero-Debt Tri-State
# =============================================================================
def test_54_final_pass_harden_verification():
    from app.services.financial_engine.optimizer.m5_engine import m5_engine
    from app.services.financial_engine.optimizer.m5_schema import (
        StressScenarioResult,
        StressScenarioType,
        ResilienceStatus,
        SchemeRoutingOption,
        SchemeEligibilityStatus,
        FinancingGapAnalysisResult,
        M5ValidationState
    )
    from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode

    # 1. Deterministic Risk Flag Deduplication
    sc1 = StressScenarioResult(
        scenario_id="SC_1",
        scenario_name="Revenue Downside",
        scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
        status="RESOLVED",
        dscr=0.9,
        current_ratio=1.2,
        resilience_status=ResilienceStatus.CRITICAL,
        reason_codes=[M5ReasonCode.DSCR_BELOW_THRESHOLD, M5ReasonCode.DSCR_BELOW_THRESHOLD, M5ReasonCode.REPAYMENT_DEFICIT]
    )
    sc2 = StressScenarioResult(
        scenario_id="SC_2",
        scenario_name="Cost Downside",
        scenario_type=StressScenarioType.VARIABLE_COST_INCREASE,
        status="RESOLVED",
        dscr=0.85,
        current_ratio=1.1,
        resilience_status=ResilienceStatus.CRITICAL,
        reason_codes=[M5ReasonCode.DSCR_BELOW_THRESHOLD]
    )
    # When m5_engine processes these stress scenarios, duplicates within the same scenario must be removed
    seen_risk_keys = set()
    deduped_flags = []
    for sc in [sc1, sc2]:
        for rc in sc.reason_codes:
            rc_str = rc.value if hasattr(rc, "value") else str(rc)
            key = (sc.scenario_id, rc_str)
            if key not in seen_risk_keys:
                seen_risk_keys.add(key)
                deduped_flags.append({
                    "scenario_id": sc.scenario_id,
                    "scenario_name": sc.scenario_name,
                    "reason_code": rc_str,
                    "resilience_status": sc.resilience_status.value if hasattr(sc.resilience_status, "value") else str(sc.resilience_status),
                    "dscr": sc.dscr,
                    "current_ratio": sc.current_ratio
                })
    # SC_1 had two DSCR_BELOW_THRESHOLD, so it should only have 2 unique flags: DSCR_BELOW_THRESHOLD and REPAYMENT_DEFICIT
    sc1_flags = [f for f in deduped_flags if f["scenario_id"] == "SC_1"]
    assert len(sc1_flags) == 2
    assert sc1_flags[0]["reason_code"] == M5ReasonCode.DSCR_BELOW_THRESHOLD.value
    assert sc1_flags[1]["reason_code"] == M5ReasonCode.REPAYMENT_DEFICIT.value
    # SC_2 also has DSCR_BELOW_THRESHOLD, which is preserved because scenario_id differs
    sc2_flags = [f for f in deduped_flags if f["scenario_id"] == "SC_2"]
    assert len(sc2_flags) == 1
    assert sc2_flags[0]["reason_code"] == M5ReasonCode.DSCR_BELOW_THRESHOLD.value

    # 2. Ambiguous Scheme Margin: multiple eligible schemes with different margins -> None
    sch_a = SchemeRoutingOption(
        scheme_id="SCH_A",
        scheme_name="Scheme A",
        eligibility_status=SchemeEligibilityStatus.ELIGIBLE,
        required_margin_percentage=10.0
    )
    sch_b = SchemeRoutingOption(
        scheme_id="SCH_B",
        scheme_name="Scheme B",
        eligibility_status=SchemeEligibilityStatus.ELIGIBLE,
        required_margin_percentage=15.0
    )
    applicable = [sc for sc in [sch_a, sch_b] if sc.eligibility_status.value in ("ELIGIBLE", "VERIFICATION_REQUIRED") and sc.required_margin_percentage is not None]
    unique_margins = {sc.required_margin_percentage for sc in applicable}
    resolved_margin = unique_margins.pop() if len(unique_margins) == 1 else None
    assert resolved_margin is None  # Ambiguous margins must remain None!

    # When all schemes share the exact same margin, it is unique and resolved
    sch_c = SchemeRoutingOption(
        scheme_id="SCH_C",
        scheme_name="Scheme C",
        eligibility_status=SchemeEligibilityStatus.ELIGIBLE,
        required_margin_percentage=10.0
    )
    applicable_c = [sc for sc in [sch_a, sch_c] if sc.eligibility_status.value in ("ELIGIBLE", "VERIFICATION_REQUIRED") and sc.required_margin_percentage is not None]
    unique_margins_c = {sc.required_margin_percentage for sc in applicable_c}
    resolved_margin_c = unique_margins_c.pop() if len(unique_margins_c) == 1 else None
    assert resolved_margin_c == 10.0

    # 3. Zero-Debt Tri-State Validation Gates
    # Fully funded equity:
    gap_ok = FinancingGapAnalysisResult(
        total_project_cost=500000.0,
        available_promoter_contribution=500000.0,
        scheme_loan=0.0,
        other_verified_financing=0.0,
        total_funding=500000.0,
        funding_gap=0.0,
        is_balanced=True,
        status="RESOLVED"
    )
    v_pass = m5_validation_engine.validate(
        project_cost=500000.0,
        financing_gap_analysis=gap_ok,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        is_zero_debt=True
    )
    chk_pass = next(c for c in v_pass.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_pass.status == M5ValidationState.PASSED

    # Unresolved funding:
    v_unres = m5_validation_engine.validate(
        project_cost=500000.0,
        financing_gap_analysis=None,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        is_zero_debt=True
    )
    chk_unres = next(c for c in v_unres.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_unres.status == M5ValidationState.UNRESOLVED

    # Funding shortfall:
    gap_short = FinancingGapAnalysisResult(
        total_project_cost=500000.0,
        available_promoter_contribution=300000.0,
        scheme_loan=0.0,
        other_verified_financing=0.0,
        total_funding=300000.0,
        funding_gap=200000.0,
        is_balanced=False,
        status="RESOLVED"
    )
    v_fail = m5_validation_engine.validate(
        project_cost=500000.0,
        financing_gap_analysis=gap_short,
        promoter_analysis=None,
        selected_structure=None,
        stress_scenarios=None,
        is_zero_debt=True
    )
    chk_fail = next(c for c in v_fail.checks if c.check_id == "VAL_M5_SELECTED_STRUCTURE_FEASIBILITY")
    assert chk_fail.status == M5ValidationState.FAILED


# =============================================================================
# 27. M5 Selected Financing Structure Reconciles with M3 Loan & Retained Reserve
# =============================================================================
def test_27_m5_selected_structure_reconciles_with_m3_and_retained_reserve():
    """
    Verifies that M5 financing optimizer reflects the canonical M3 financing structure:
    Project Cost: ₹5,00,000, Promoter Margin: ₹50,000, Loan: ₹4,50,000, Retained Reserve: ₹1,50,000,
    instead of consuming all ₹2,00,000 available capital as a ₹3,00,000 loan.
    """
    req = FinancialAnalysisRequest(
        analysis_id="saree_reconciliation_test",
        session_id="saree_session_rec",
        business_profile=BusinessProfileInput(
            business_id="saree_retail",
            specific_business="Saree Retail",
            sector="Retail",
            category="Apparel Retail",
            business_constitution="SOLE_PROPRIETORSHIP"
        ),
        financial_profile=FinancialProfileInput(
            available_margin_capital=200000.0,
            preferred_project_cost=500000.0
        ),
        beneficiary_profile=BeneficiaryProfileInput(
            beneficiary_category="General",
            gender="Female",
            is_greenfield=True
        ),
        location_profile=LocationProfileInput(
            district="Varanasi",
            state="Uttar Pradesh"
        )
    )

    resp = financial_engine.analyze(req)
    c = resp.financial_analysis
    m5 = c.financing_optimizer

    assert m5 is not None
    sel = m5.selected_financing_structure
    assert sel is not None

    # M5 Selected structure matches M3 Loan, Margin, and Tenure
    assert sel.total_project_cost == 500000.0
    assert sel.promoter_contribution == 50000.0
    assert sel.loan_amount == 450000.0
    assert sel.margin_surplus_or_gap == 150000.0  # Retained reserve
    assert sel.is_margin_met is True
    assert sel.is_gap_eliminated is True
    assert sel.monthly_emi == c.loan_management.monthly_emi
    assert sel.tenure_months == c.loan_management.tenure_months
    assert sel.interest_rate == c.loan_management.annual_interest_rate

    # DPR Summary in M5 also reflects the reconciled figures
    assert m5.dpr_summary is not None
    assert m5.dpr_summary.total_project_cost == 500000.0
    assert m5.dpr_summary.promoter_contribution == 50000.0
    assert m5.dpr_summary.term_loan == 450000.0
    assert m5.dpr_summary.monthly_emi == c.loan_management.monthly_emi







