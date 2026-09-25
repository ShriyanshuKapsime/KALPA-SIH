"""
Milestone 3 Test Suite: Financial Projection & Statement Engine.
Covers all 22 required test cases:
1. 5-year revenue projection
2. Revenue = volume × price
3. COGS calculation
4. P&L accounting identity
5. Depreciation schedule
6. Loan interest reconciles with Stage 9 amortization
7. Debt balance reconciliation
8. Working-capital projection
9. Cash-flow reconciliation
10. Balance-sheet balances
11. Sources = Uses
12. UNKNOWN input does not become zero
13. Explicit zero remains zero
14. Missing tax does not fabricate tax
15. Missing growth does not fabricate growth
16. M2 project cost flows into M3
17. M3 outputs appear in Stage 9 response
18. Existing Stage 9 behavior remains compatible
19. Base scenario works
20. Scenario parameters are deterministic
21. Ratio zero-denominator handling
22. Validation diagnostics work
"""
import pytest
from typing import Dict, Any, List, Optional

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    ProjectAssumptionsInput,
    FinancialAnalysisContainer,
    FinancialProjection,
    ProfitLossStatement,
    BalanceSheet,
    CashFlowStatement,
    WorkingCapitalProjection,
    FinancialRatioSet,
    FundingSourcesUses,
    ProjectionValidation,
    ProjectCostAnalysis,
    ProfitLossYear,
    BalanceSheetYear,
    CashFlowYear,
    WorkingCapitalYear,
    DepreciationScheduleYear,
)
from app.services.financial_engine.engine import financial_engine
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype
from app.services.financial_engine.intelligence.confidence import ResolvedAssumption, SourceType, AssumptionStatus, AssumptionType, Provenance
from app.services.financial_engine.project_cost import project_cost_engine
from app.services.financial_engine.projection import (
    projection_engine,
    sources_uses_engine,
    revenue_projection_engine,
    cost_projection_engine,
    depreciation_engine,
    working_capital_projection_engine,
    profit_loss_engine,
    cash_flow_statement_engine,
    balance_sheet_engine,
    financial_ratios_engine,
    validation_engine,
    sensitivity_engine,
)


def _make_asm(driver_id: str, value: Any, source_type: SourceType = SourceType.USER_INPUT) -> ResolvedAssumption:
    return ResolvedAssumption(
        driver_id=driver_id,
        value=value,
        unit="INR" if "cost" in driver_id or "revenue" in driver_id or "inventory" in driver_id or "price" in driver_id else "count",
        source_type=source_type,
        source_id="TEST",
        confidence=0.90,
        status=AssumptionStatus.RESOLVED if value is not None else AssumptionStatus.UNRESOLVED,
        assumption_type=AssumptionType.USER_INPUT,
        user_confirmed=True,
        required=True,
        provenance=Provenance(source_type=source_type, source_id="TEST", description=f"Test {driver_id}", confidence=0.90)
    )


# Fixture: Small Retail Store
def _build_retail_analysis_request(tax_rate: Optional[float] = 0.0) -> FinancialAnalysisRequest:
    inputs = {
        "is_greenfield": True,
        "pre_operating_cost": 0.0,
        "contingency": 0.0,
        "monthly_units": 500.0,
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
    }
    if tax_rate is not None:
        inputs["tax_rate"] = tax_rate

    return FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(
            available_margin_capital=100000.0,
            preferred_project_cost=500000.0,
        ),
        business_profile=BusinessProfileInput(
            business_id="garment_store",
            specific_business="Retail Apparel Store",
            sector="retail",
            category="apparel",
        ),
        project_assumptions=ProjectAssumptionsInput(
            expected_monthly_revenue=150000.0,
            expected_monthly_units=500.0,
            expected_unit_price=300.0,
        ),
        user_driver_inputs=inputs
    )


# =============================================================================
# 1. 5-Year Revenue Projection
# =============================================================================
def test_01_five_year_revenue_projection():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    fp = resp.financial_analysis.financial_projection
    assert fp is not None
    assert fp.projection_years == 5
    assert len(fp.revenue_projection.years) == 5
    # Year 1 base revenue: 500 * 300 * 12 = 1,800,000
    assert fp.revenue_projection.years[0].revenue == 1800000.0
    # Year 2 at 5% growth: 1,800,000 * 1.05 = 1,890,000
    assert fp.revenue_projection.years[1].revenue == 1890000.0
    # Year 3: 1,890,000 * 1.05 = 1,984,500
    assert fp.revenue_projection.years[2].revenue == 1984500.0


# =============================================================================
# 2. Revenue = Volume × Price
# =============================================================================
def test_02_revenue_equals_volume_times_price():
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_units": 1000.0, "expected_unit_price": 250.0, "growth_rate": 0.0}
    )
    assert rev_proj.status == "RESOLVED"
    assert rev_proj.methodology == "VOLUME_X_PRICE"
    # Annual volume = 1000 * 12 = 12,000; Price = 250; Rev = 3,000,000
    for line in rev_proj.years:
        assert line.revenue == round(line.volume * line.price_per_unit, 2)
        assert line.revenue == 3000000.0


# =============================================================================
# 3. COGS Calculation
# =============================================================================
def test_03_cogs_calculation():
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0, "growth_rate": 0.0}
    )
    # Gross margin = 40% -> COGS ratio = 60%, solo business with 0 staff
    cost_proj = cost_projection_engine.project(
        revenue_projection=rev_proj,
        user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0, "staff_count": 0}
    )
    assert cost_proj.status == "RESOLVED"
    # Rev = 1,200,000 -> COGS = 720,000
    assert cost_proj.years[0].cogs == 720000.0


# =============================================================================
# 4. P&L Accounting Identity (Gross Profit, EBITDA, EBIT, PBT, PAT)
# =============================================================================
def test_04_profit_and_loss_accounting_identity():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    pl = resp.financial_analysis.profit_loss_statement
    assert pl is not None
    assert pl.status == "RESOLVED"
    for y in pl.years:
        # Gross profit = Revenue - COGS
        assert y.gross_profit == round(y.revenue - y.cogs, 2)
        # EBITDA = Gross profit - Operating expenses
        assert y.ebitda == round(y.gross_profit - y.operating_expenses, 2)
        # EBIT = EBITDA - Depreciation
        assert y.ebit == round(y.ebitda - y.depreciation, 2)
        # PBT = EBIT - Interest
        assert y.profit_before_tax == round(y.ebit - y.interest_expense, 2)


# =============================================================================
# 5. Depreciation Schedule (SLM)
# =============================================================================
def test_05_depreciation_schedule_slm():
    depr_sched = depreciation_engine.calculate_schedule(
        projection_years=5,
        user_inputs={"depreciation_life_years": 5.0},
        capital_structure=None,
        project_cost_analysis=None,
    )
    # With explicit capex
    from app.schemas.financial_analysis import CapitalStructure
    cs = CapitalStructure(
        total_project_cost=500000.0,
        fixed_capital_capex=250000.0,
        working_capital=250000.0,
        margin_contribution=50000.0,
        loan_component=450000.0,
    )
    sched = depreciation_engine.calculate_schedule(
        projection_years=5,
        capital_structure=cs,
        useful_life_years=5.0
    )
    # 250,000 / 5 = 50,000 per year
    assert sched[1].depreciation_amount == 50000.0
    assert sched[1].accumulated_depreciation == 50000.0
    assert sched[1].net_block == 200000.0

    assert sched[5].accumulated_depreciation == 250000.0
    assert sched[5].net_block == 0.0


# =============================================================================
# 6. Loan Interest Reconciles with Stage 9 Amortization
# =============================================================================
def test_06_loan_interest_reconciles_with_stage9_amortization():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis
    pl = fa.profit_loss_statement
    repay = fa.repayment

    # Sum of monthly interest in repayment schedule for years 1-5
    for y_idx, pl_year in enumerate(pl.years, start=1):
        months_in_year = [r for r in repay.monthly_schedule if (r.period - 1) // 12 + 1 == y_idx]
        sched_int = sum(float(r.interest_component) for r in months_in_year)
        assert abs(pl_year.interest_expense - round(sched_int, 2)) <= 0.05


# =============================================================================
# 7. Debt Balance Reconciliation
# =============================================================================
def test_07_debt_balance_reconciliation():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    val = resp.financial_analysis.financial_projection.validation
    debt_check = next(c for c in val.checks if c.check_id == "CHECK_4_DEBT_REDUCTION")
    assert debt_check.status == "PASSED"
    assert debt_check.difference <= 1.0


# =============================================================================
# 8. Working-Capital Projection
# =============================================================================
def test_08_working_capital_projection():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    wc_proj = resp.financial_analysis.working_capital_projection
    assert wc_proj is not None
    assert wc_proj.status == "RESOLVED"
    assert len(wc_proj.years) == 5
    # Inventory, receivables, and payables are resolved
    for y in wc_proj.years:
        assert y.inventory is not None and y.inventory > 0
        assert y.receivables is not None and y.receivables > 0
        assert y.payables is not None and y.payables > 0
        assert y.net_working_capital == round(y.inventory + y.receivables - y.payables, 2)


# =============================================================================
# 9. Cash-Flow Reconciliation
# =============================================================================
def test_09_cash_flow_reconciliation():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    cf = resp.financial_analysis.cash_flow_statement
    assert cf is not None
    assert cf.status == "RESOLVED"
    for y in cf.years:
        assert y.closing_cash_balance == round(y.opening_cash_balance + y.net_change_in_cash, 2)


# =============================================================================
# 10. Balance-Sheet Balances (Assets == Liabilities + Equity)
# =============================================================================
def test_10_balance_sheet_balances():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    bs = resp.financial_analysis.balance_sheet
    assert bs is not None
    assert bs.status == "BALANCED"
    for y in bs.years:
        assert y.is_balanced is True
        assert abs(y.reconciliation_difference) <= 1.0


# =============================================================================
# 11. Sources = Uses
# =============================================================================
def test_11_sources_equal_uses():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    su = resp.financial_analysis.funding_sources_uses
    assert su is not None
    assert su.status == "RECONCILED"
    assert abs(su.difference) <= 1.0


# =============================================================================
# 12. UNKNOWN Input Does Not Become Zero
# =============================================================================
def test_12_unknown_input_does_not_become_zero():
    # Calling cost projection without salary or rent assumptions
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0}
    )
    cost_proj = cost_projection_engine.project(
        revenue_projection=rev_proj,
        user_inputs={}  # No salary, no rent, no opex
    )
    # Unprovided expenses must remain None, NOT 0.0!
    assert cost_proj.years[0].salaries_wages is None
    assert cost_proj.years[0].rent is None
    assert cost_proj.years[0].marketing is None


# =============================================================================
# 13. Explicit Zero Remains Zero
# =============================================================================
def test_13_explicit_zero_remains_zero():
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0}
    )
    # Explicit solo business: staff_count = 0
    cost_proj = cost_projection_engine.project(
        revenue_projection=rev_proj,
        user_inputs={"staff_count": 0}
    )
    assert cost_proj.years[0].salaries_wages == 0.0


# =============================================================================
# 14. Missing Tax Does Not Fabricate Tax
# =============================================================================
def test_14_missing_tax_does_not_fabricate_tax():
    req = _build_retail_analysis_request(tax_rate=None)
    resp = financial_engine.analyze(req)
    pl = resp.financial_analysis.profit_loss_statement
    # Tax rate was not in user input, so tax should be PROVISIONAL_PENDING_REGISTRATION / NOT_MODELED, not fabricated 25% or 30%
    assert pl.years[0].tax_status in ("PROVISIONAL_PENDING_REGISTRATION", "NOT_MODELED")
    assert pl.years[0].tax_expense is None
    assert pl.years[0].profit_after_tax is None


# =============================================================================
# 15. Missing Growth Does Not Fabricate Growth
# =============================================================================
def test_15_missing_growth_does_not_fabricate_growth():
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0},
        allow_flat_base_case=False  # Disallow flat base case
    )
    # When growth cannot be assumed flat and is missing, it must be marked UNKNOWN
    assert rev_proj.years[1].growth_source == "UNKNOWN"
    assert rev_proj.years[1].revenue is None


# =============================================================================
# 16. M2 Project Cost Flows into M3
# =============================================================================
def test_16_m2_project_cost_flows_into_m3():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis
    pc = fa.project_cost_analysis
    su = fa.funding_sources_uses

    assert pc is not None
    assert su is not None
    # CapEx in Sources & Uses matches M2 CapEx
    assert su.capex == pc.capex
    # Opening inventory in Sources & Uses matches M2 Opening Inventory
    assert su.opening_inventory == pc.opening_inventory


# =============================================================================
# 17. M3 Outputs Appear in Stage 9 Response
# =============================================================================
def test_17_m3_outputs_appear_in_stage9_response():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    assert fa.financial_projection is not None
    assert fa.profit_loss_statement is not None
    assert fa.cash_flow_statement is not None
    assert fa.balance_sheet is not None
    assert fa.working_capital_projection is not None
    assert fa.financial_ratios is not None
    assert fa.funding_sources_uses is not None
    assert fa.projection_validation is not None
    assert fa.projection_provenance is not None
    assert len(fa.projection_provenance) > 0


# =============================================================================
# 18. Existing Stage 9 Behavior Remains Compatible
# =============================================================================
def test_18_existing_stage9_behavior_remains_compatible():
    # Legacy minimal request without M1/M2/M3 inputs
    req = FinancialAnalysisRequest(
        financial_profile=FinancialProfileInput(available_margin_capital=50000.0),
        business_profile=BusinessProfileInput(business_id="tailoring_shop", specific_business="Tailoring"),
    )
    resp = financial_engine.analyze(req)
    assert resp.financial_analysis.scheme_result is not None
    assert resp.financial_analysis.profitability is not None
    assert resp.financial_analysis.financial_viability is not None
    assert resp.financial_analysis.financial_projection is not None


# =============================================================================
# 19. Base Scenario Works
# =============================================================================
def test_19_base_scenario_works():
    scenarios = sensitivity_engine.evaluate_scenarios(
        base_annual_revenue=1000000.0,
        base_annual_cogs=600000.0,
        base_annual_opex=200000.0,
        scenario_inputs=None
    )
    assert "BASE" in scenarios
    assert scenarios["BASE"]["revenue"] == 1000000.0
    assert scenarios["BASE"]["ebitda"] == 200000.0


# =============================================================================
# 20. Scenario Parameters are Deterministic
# =============================================================================
def test_20_scenario_parameters_are_deterministic():
    cfg = {
        "UPSIDE": {"revenue_adjustment": 0.10, "cost_adjustment": 0.0, "description": "10% growth"},
        "DOWNSIDE": {"revenue_adjustment": -0.10, "cost_adjustment": 0.05, "description": "10% drop, 5% cost inflation"}
    }
    scenarios = sensitivity_engine.evaluate_scenarios(
        base_annual_revenue=1000000.0,
        base_annual_cogs=600000.0,
        base_annual_opex=200000.0,
        scenario_inputs=cfg
    )
    assert "UPSIDE" in scenarios
    assert scenarios["UPSIDE"]["revenue"] == 1100000.0
    assert "DOWNSIDE" in scenarios
    assert scenarios["DOWNSIDE"]["revenue"] == 900000.0
    assert scenarios["DOWNSIDE"]["cogs"] == 630000.0


# =============================================================================
# 21. Ratio Zero-Denominator Handling
# =============================================================================
def test_21_ratio_zero_denominator_handling():
    # Test safe division directly in ratios engine when revenue = 0 or assets = 0
    from app.schemas.financial_analysis import ProfitLossYear, BalanceSheetYear, CashFlowYear, WorkingCapitalYear
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, revenue=0.0, gross_profit=0.0, ebitda=0.0, ebit=0.0, profit_before_tax=0.0, profit_after_tax=0.0)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1, total_assets=0.0, total_equity=0.0, total_current_assets=0.0, trade_payables=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, net_working_capital=0.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, principal_repayment=0.0)])

    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    r1 = ratios.years[0]
    # Denominator zero should return None, NOT raise ZeroDivisionError
    assert r1.gross_margin is None
    assert r1.net_profit_margin is None
    assert r1.return_on_assets is None
    assert r1.return_on_equity is None


# =============================================================================
# 22. Validation Diagnostics Work
# =============================================================================
def test_22_validation_diagnostics_work():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    val = resp.financial_analysis.financial_projection.validation
    assert val is not None
    assert val.total_checks == 12
    assert val.all_passed is True
    # Verify each check has required diagnostic fields
    for c in val.checks:
        assert c.check_id.startswith("CHECK_")
        assert c.status in ("PASSED", "FAILED", "WARNING", "UNRESOLVED")
        assert c.message is not None
        assert len(c.message) > 0


# =============================================================================
# 23. Hardening: Depreciation Useful Life Missing (No 10-Year Fallback)
# =============================================================================
def test_23_depreciation_no_ten_year_fallback():
    from app.services.financial_engine.projection.depreciation import depreciation_engine
    schedule = depreciation_engine.calculate_schedule(
        projection_years=5,
        project_cost_analysis=None,
        capital_structure=None,
        user_inputs={}
    )
    # With no capex and no asset life, schedule must not fabricate 10 years or 10% rate
    assert schedule[1].status == "UNKNOWN"
    assert schedule[1].depreciation_amount is None


# =============================================================================
# 24. Hardening: Revenue Operating Days Missing (No 25-Day Fallback)
# =============================================================================
def test_24_revenue_no_twenty_five_day_fallback():
    # When user only provides daily revenue but no operating days, do not invent 25 days
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"daily_revenue": 5000.0}  # No operating_days_per_month provided
    )
    assert rev_proj.status in ("UNKNOWN", "PARTIALLY_DERIVED", "INSUFFICIENT_DATA")
    assert rev_proj.base_annual_revenue is None
    for y in rev_proj.years:
        assert y.revenue is None


# =============================================================================
# 25. Hardening: Working Capital Propagates None (No Zero Substitution)
# =============================================================================
def test_25_working_capital_propagates_none():
    # Only revenue provided, but no turnover days or inventory estimates
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0}
    )
    wc_proj = working_capital_projection_engine.project(
        revenue_projection=rev_proj,
        cost_projection=None,
        working_capital_analysis=None,
        project_cost_analysis=None,
        benchmark_data=None,
        user_inputs={},
        assumptions_map={}
    )
    assert wc_proj.status in ("UNKNOWN", "PARTIALLY_DERIVED")
    # Missing inventory and payables days must NOT silently default to 0 days or 0 values
    for y in wc_proj.years:
        assert y.net_working_capital is None
        assert y.change_in_working_capital is None


# =============================================================================
# 26. Hardening: Cash Flow Propagates Unknown Delta WC (Not Zeroed)
# =============================================================================
def test_26_cash_flow_propagates_unknown_delta_wc():
    from app.schemas.financial_analysis import ProfitLossYear, WorkingCapitalYear
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0, depreciation=10000.0)])
    # Change in working capital is None
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=None)])
    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=sources_uses_engine.build(project_cost_analysis=None, user_inputs={}),
        repayment_schedule=None
    )
    # CFO cannot be computed when Delta WC is unknown
    assert cf.years[0].cash_from_operations is None
    assert cf.years[0].closing_cash_balance is None


# =============================================================================
# 27. Hardening: Ratios Remove 10.0 Fallback on Zero Denominators
# =============================================================================
def test_27_ratios_remove_ten_point_zero_fallback():
    from app.schemas.financial_analysis import ProfitLossYear, BalanceSheetYear, CashFlowYear, WorkingCapitalYear
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, revenue=100000.0, ebitda=20000.0, ebit=20000.0, interest_expense=0.0, profit_after_tax=15000.0)])
    # Zero current liabilities
    bs = BalanceSheet(years=[BalanceSheetYear(year=1, total_current_assets=50000.0, trade_payables=0.0, total_liabilities=0.0, total_equity=50000.0, total_assets=50000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, net_working_capital=50000.0)])
    # Zero debt service
    cf = CashFlowStatement(years=[CashFlowYear(year=1, principal_repayment=0.0)])

    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    r1 = ratios.years[0]
    # In institutional finance: Zero liabilities with positive current assets does NOT equal 10.0
    assert r1.current_ratio is None
    # Zero interest with positive EBIT does NOT equal 10.0
    assert r1.interest_coverage is None
    # Zero debt service with positive cash flow does NOT equal 10.0
    assert r1.dscr is None


# =============================================================================
# 28. Hardening: Sources & Uses Returns None (No Fake Zero Totals)
# =============================================================================
def test_28_sources_uses_no_fake_zero():
    su = sources_uses_engine.build(
        project_cost_analysis=None,
        capital_structure=None,
        project_financing=None,
        user_inputs={}
    )
    assert su.total_uses is None
    assert su.total_sources is None
    assert su.difference is None
    assert su.status == "INSUFFICIENT_DATA"


# =============================================================================
# 29. Hardening: Sensitivity Scope Tagged as Operating-Level Only
# =============================================================================
def test_29_sensitivity_scoped_as_operating_level():
    res = sensitivity_engine.evaluate_scenarios(
        base_annual_revenue=500000.0,
        base_annual_cogs=250000.0,
        base_annual_opex=100000.0
    )
    assert res["BASE"]["scope"] == "OPERATING_LEVEL_ONLY"
    assert "M4" in res["BASE"]["scope_note"]


# =============================================================================
# 30. Hardening: Validation Handles Missing Data Without Crashing
# =============================================================================
def test_30_validation_handles_missing_data_gracefully():
    # Completely empty/unresolved statements
    su = sources_uses_engine.build(project_cost_analysis=None, user_inputs={})
    bs = BalanceSheet(years=[])
    cf = CashFlowStatement(years=[])
    pl = ProfitLossStatement(years=[])
    wc = WorkingCapitalProjection(years=[])
    ratios = FinancialRatioSet(years=[])

    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    assert val is not None
    assert val.total_checks == 12
    # Should flag checks as failed or unresolved, never crash with TypeError
    assert val.all_passed is False


# =============================================================================
# INSTITUTIONAL HARDENING SPECIFIC TEST SUITE (15 Critical Requirements)
# =============================================================================

def test_hardening_01_missing_promoter_contribution_does_not_become_zero():
    """1. Missing promoter contribution does not become zero."""
    su = FundingSourcesUses(
        status="PARTIALLY_DERIVED",
        promoter_contribution=None,
        term_loan=300000.0,
        capex=250000.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, closing_cash_balance=20000.0, principal_repayment=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, inventory=10000.0, receivables=5000.0, payables=4000.0)])

    bs = balance_sheet_engine.generate(
        profit_loss=pl,
        cash_flow=cf,
        working_capital_proj=wc,
        sources_uses=su,
        depreciation_schedule={}
    )
    # Promoter capital and total equity must be None, NOT 0.0
    assert bs.years[0].promoter_capital is None
    assert bs.years[0].total_equity is None


def test_hardening_02_incomplete_year0_cash_flow_remains_unresolved():
    """2. Incomplete Year-0 cash flow remains unresolved."""
    su = FundingSourcesUses(
        status="INSUFFICIENT_DATA",
        promoter_contribution=None,
        term_loan=300000.0,
        capex=250000.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])

    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=su
    )
    # Closing cash 0 must be None
    assert cf.year_0_deployment["closing_cash_balance"] is None
    # Year 1 opening and closing cash must be None
    assert cf.years[0].opening_cash_balance is None
    assert cf.years[0].closing_cash_balance is None
    assert cf.status == "PARTIALLY_DERIVED"


def test_hardening_03_missing_opening_receivables_payables_remain_unknown():
    """3. Missing opening receivables/payables remain unknown."""
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0}
    )
    wc = working_capital_projection_engine.project(
        revenue_projection=rev_proj,
        cost_projection=None,
        working_capital_analysis=None,
        project_cost_analysis=None,
        benchmark_data=None,
        user_inputs={"is_greenfield": False}
    )
    # Day 0 baseline unknown prevents delta_nwc contamination
    assert wc.years[0].change_in_working_capital is None


def test_hardening_04_unknown_tax_pat_is_none():
    """4. Unknown tax -> PAT=None."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    cost = cost_projection_engine.project(rev, user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0, "staff_count": 0})
    pl = profit_loss_engine.generate(rev, cost, {}, user_inputs={})
    for y in pl.years:
        assert y.tax_status == "NOT_MODELED"
        assert y.tax_expense is None
        assert y.profit_after_tax is None


def test_hardening_05_explicit_zero_tax_pat_equals_pbt():
    """5. Explicit zero tax -> PAT=PBT."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    cost = cost_projection_engine.project(rev, user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0, "staff_count": 0})
    # Fully resolved PBT requires resolved depreciation and interest
    su = FundingSourcesUses(status="RECONCILED", term_loan=0.0)
    depr_map = {y.year: type("D", (), {"depreciation_amount": 0.0})() for y in rev.years}
    pl = profit_loss_engine.generate(rev, cost, depr_map, sources_uses=su, user_inputs={"tax_rate": 0.0})
    for y in pl.years:
        assert y.tax_status in ("EXEMPT", "CALCULATED")
        assert y.tax_expense == 0.0
        assert y.profit_after_tax == y.profit_before_tax


def test_hardening_06_benchmark_useful_life_reaches_depreciation():
    """6. Benchmark/assumption useful life reaches DepreciationEngine through ProjectionEngine."""
    b_data = {
        "sector": "retail",
        "category": "apparel",
        "depreciation_rate": 12.5,
        "depreciation_life_years": 8.0,
    }
    res = projection_engine.project(
        projection_years=5,
        user_inputs={"monthly_revenue": 100000.0, "capex_override": 200000.0},
        benchmark_data=b_data,
        assumptions_map={}
    )
    # 12.5% depreciation rate -> 8 years useful life on 200,000 capex -> 25,000 annual depreciation
    assert res.profit_loss_statement.years[0].depreciation == 25000.0


def test_hardening_07_unknown_opex_prevents_false_total():
    """7. Unknown OPEX component prevents false total OPEX."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    # Rent is provided, but salary is unknown and no Stage 9 aggregate OPEX
    cost = cost_projection_engine.project(rev, user_inputs={"monthly_rent": 10000.0})
    assert cost.years[0].rent == 120000.0
    assert cost.years[0].salaries_wages is None
    assert cost.years[0].total_operating_expenses is None
    assert cost.status == "PARTIALLY_DERIVED"


def test_hardening_08_unknown_dscr_dependency_yields_none():
    """8. Unknown DSCR dependency -> DSCR=None."""
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0, depreciation=10000.0, interest_expense=None)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1, total_current_assets=50000.0, total_liabilities=20000.0, total_equity=30000.0, total_assets=50000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, net_working_capital=20000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, principal_repayment=25000.0)])

    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    # With unknown interest, DSCR cannot be computed
    assert ratios.years[0].dscr is None


def test_hardening_09_debt_with_unresolved_interest_yields_none():
    """9. Debt with unresolved interest -> interest=None."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    cost = cost_projection_engine.project(rev, user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0, "staff_count": 0})
    su = FundingSourcesUses(
        status="RECONCILED",
        total_sources=500000.0,
        total_uses=500000.0,
        term_loan=300000.0,
        promoter_contribution=200000.0
    )
    # Term loan is 300,000, but repayment schedule is None and user provides no interest
    pl = profit_loss_engine.generate(rev, cost, {}, repayment_schedule=None, sources_uses=su, user_inputs={})
    assert pl.years[0].interest_expense is None
    assert pl.years[0].profit_before_tax is None


def test_hardening_10_pre_op_amortization_does_not_assume_five_years():
    """10. Pre-op amortization does not assume 5 years without explicit basis."""
    su = FundingSourcesUses(
        status="RECONCILED",
        total_sources=500000.0,
        total_uses=500000.0,
        promoter_contribution=200000.0,
        term_loan=300000.0,
        capex=450000.0,
        pre_operating_cost=50000.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, closing_cash_balance=20000.0, principal_repayment=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, inventory=10000.0, receivables=5000.0, payables=4000.0)])

    # No pre_op_amortization_years provided in user_inputs or assumptions
    bs = balance_sheet_engine.generate(
        profit_loss=pl,
        cash_flow=cf,
        working_capital_proj=wc,
        sources_uses=su,
        depreciation_schedule={},
        user_inputs={},
        assumptions_map={}
    )
    # unamortized_pre_op should NOT default to 50000 - (50000/5)*1 = 40000
    assert bs.years[0].other_current_assets is None


def test_hardening_11_unknown_scenario_input_not_zero():
    """11. Unknown scenario input does not become zero."""
    res = sensitivity_engine.evaluate_scenarios(
        base_annual_revenue=None,
        base_annual_cogs=None,
        base_annual_opex=None
    )
    assert res["BASE"]["status"] == "NOT_EVALUABLE"
    assert res["BASE"]["revenue"] is None
    assert res["BASE"]["ebitda"] is None


def test_hardening_12_validation_returns_unresolved_when_insufficient_data():
    """12. Validation returns UNRESOLVED rather than PASSED when data is insufficient."""
    su = FundingSourcesUses(status="INSUFFICIENT_DATA", total_sources=None, total_uses=None)
    bs = BalanceSheet(years=[BalanceSheetYear(year=1, total_assets=None, total_liabilities_and_equity=None)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, opening_cash_balance=None, closing_cash_balance=None)])
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=None)])
    wc = WorkingCapitalProjection(years=[])
    ratios = FinancialRatioSet(years=[])

    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    assert val.all_passed is False
    assert val.unresolved_checks > 0
    unresolved_ids = [c.check_id for c in val.checks if c.status == "UNRESOLVED"]
    assert "CHECK_1_SOURCES_USES" in unresolved_ids
    assert "CHECK_2_BALANCE_SHEET_EQUALITY" in unresolved_ids


def test_hardening_13_fully_specified_fixture_produces_consistent_statements():
    """13. Fully specified fixture produces internally consistent Year 0 -> Year 5 statements."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    fp = resp.financial_analysis.financial_projection
    assert fp is not None
    assert fp.validation.all_passed is True
    assert fp.validation.failed_checks == 0
    assert fp.validation.unresolved_checks == 0
    assert resp.financial_analysis.balance_sheet.status == "BALANCED"
    assert resp.financial_analysis.cash_flow_statement.status == "RESOLVED"
    assert resp.financial_analysis.profit_loss_statement.status == "RESOLVED"


def test_hardening_14_stage9_repayment_schedule_reconciles():
    """14. Stage 9 repayment schedule reconciles correctly."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    val = resp.financial_analysis.financial_projection.validation
    check_5 = next(c for c in val.checks if c.check_id == "CHECK_5_STAGE9_LOAN_RECONCILIATION")
    assert check_5.status == "PASSED"
    assert check_5.difference is not None and check_5.difference <= 1.0


def test_hardening_15_m2_to_m3_propagation():
    """15. M2 -> M3 project cost / WC / financing propagation works."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis
    assert fa.funding_sources_uses is not None
    assert fa.funding_sources_uses.capex == fa.project_cost_analysis.capex
    assert fa.balance_sheet.years[0].gross_fixed_assets == fa.project_cost_analysis.capex


# =============================================================================
# FREEZE VERIFICATION SUITE: CRITERIA A THROUGH M
# =============================================================================

def test_freeze_A_sources_uses_unknown_wc_no_partial_total():
    """A. Sources & Uses with unknown WC does not calculate partial total uses."""
    su = sources_uses_engine.build(
        project_cost_analysis=ProjectCostAnalysis(
            status="PARTIALLY_DERIVED",
            total_project_cost=None,
            capex=200000.0,
            opening_inventory=50000.0,
            working_capital=None,
            pre_operating_cost=0.0,
            contingency=0.0,
        )
    )
    assert su.total_uses is None
    assert su.status in ("INSUFFICIENT_DATA", "PARTIALLY_DERIVED")


def test_freeze_B_year0_missing_components_unresolved():
    """B. Year-0 missing inventory/pre-op/contingency remains unresolved."""
    su = FundingSourcesUses(
        status="PARTIALLY_DERIVED",
        promoter_contribution=50000.0,
        term_loan=150000.0,
        capex=100000.0,
        opening_inventory=None,  # missing inventory
        pre_operating_cost=0.0,
        contingency=0.0,
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=10000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(profit_loss=pl, working_capital_proj=wc, sources_uses=su)
    assert cf.year_0_deployment["closing_cash_balance"] is None
    assert cf.years[0].opening_cash_balance is None
    assert cf.years[0].closing_cash_balance is None


def test_freeze_C_year0_funding_shortfall_not_clamped_to_zero():
    """C. Year-0 funding shortfall is not clamped to zero."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=20000.0,
        term_loan=80000.0,  # Sources = 100,000
        capex=100000.0,
        opening_inventory=30000.0,
        pre_operating_cost=0.0,
        contingency=0.0,  # Uses = 130,000 -> shortfall of 30,000
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=10000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(profit_loss=pl, working_capital_proj=wc, sources_uses=su)
    assert cf.year_0_deployment["closing_cash_balance"] == -30000.0


def test_freeze_D_debt_exists_no_schedule_yields_none_repayment():
    """D. Debt exists + no Stage 9 schedule -> principal repayment None."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=50000.0,
        term_loan=200000.0,
        capex=150000.0,
        opening_inventory=50000.0,
        pre_operating_cost=0.0,
        contingency=0.0,
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=20000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=su,
        repayment_schedule=None,  # No schedule
    )
    assert cf.years[0].principal_repayment is None
    assert cf.years[0].closing_cash_balance is None
    assert cf.years[0].status == "PARTIALLY_DERIVED"


def test_freeze_E_debt_zero_yields_zero_repayment():
    """E. Debt = 0 -> principal repayment 0."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=200000.0,
        term_loan=0.0,
        capex=150000.0,
        opening_inventory=50000.0,
        pre_operating_cost=0.0,
        contingency=0.0,
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=20000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=su,
        repayment_schedule=None,
    )
    assert cf.years[0].principal_repayment == 0.0


def test_freeze_F_missing_is_greenfield_does_not_create_zero_receivables_payables():
    """F. Missing is_greenfield does not create zero receivables/payables."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    wc = working_capital_projection_engine.project(
        revenue_projection=rev,
        cost_projection=None,
        user_inputs={},  # No is_greenfield
    )
    assert wc.years[0].change_in_working_capital is None


def test_freeze_G_explicit_is_greenfield_produces_structural_zero():
    """G. Explicit is_greenfield=True produces structural zero."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    wc = working_capital_projection_engine.project(
        revenue_projection=rev,
        cost_projection=None,
        user_inputs={"is_greenfield": True},
    )
    assert wc.status in ("RESOLVED", "PARTIALLY_DERIVED")


def test_freeze_H_projection_engine_passes_assumptions_to_balance_sheet():
    """H. ProjectionEngine passes assumptions_map to BalanceSheetEngine."""
    fp = projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0, "is_greenfield": True, "pre_operating_cost": 50000.0, "contingency": 0.0},
        assumptions_map={
            "pre_op_amortization_years": _make_asm("pre_op_amortization_years", 5.0, SourceType.BENCHMARK)
        }
    )
    assert fp.balance_sheet.years[0].other_current_assets == 40000.0


def test_freeze_I_missing_bs_inputs_yields_partially_derived_not_failed():
    """I. Missing BS inputs -> PARTIALLY_DERIVED, not FAILED."""
    su = FundingSourcesUses(
        status="PARTIALLY_DERIVED",
        promoter_contribution=None,  # Missing equity
        term_loan=200000.0,
        capex=150000.0,
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=20000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, closing_cash_balance=10000.0, principal_repayment=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, inventory=10000.0, receivables=5000.0, payables=4000.0)])
    bs = balance_sheet_engine.generate(
        profit_loss=pl,
        cash_flow=cf,
        working_capital_proj=wc,
        sources_uses=su,
        depreciation_schedule={},
    )
    assert bs.status == "PARTIALLY_DERIVED"
    assert bs.status != "FAILED"


def test_freeze_J_validation_failed_yields_validation_failed():
    """J. Validation FAILED -> VALIDATION_FAILED."""
    su = FundingSourcesUses(status="RECONCILED", total_sources=100000.0, total_uses=100000.0, promoter_contribution=10000.0, term_loan=90000.0)
    bs = BalanceSheet(status="FAILED", years=[BalanceSheetYear(year=1, total_assets=500000.0, total_liabilities_and_equity=100000.0, is_balanced=False, status="FAILED")])
    cf = CashFlowStatement(status="RESOLVED", years=[CashFlowYear(year=1, opening_cash_balance=0.0, net_change_in_cash=100.0, closing_cash_balance=100.0, status="RESOLVED")])
    pl = ProfitLossStatement(status="RESOLVED", years=[ProfitLossYear(year=1, revenue=1000.0, cogs=500.0, gross_profit=500.0, operating_expenses=200.0, ebitda=300.0, depreciation=50.0, ebit=250.0, interest_expense=50.0, profit_before_tax=200.0, tax_expense=0.0, profit_after_tax=200.0, status="RESOLVED")])
    wc = WorkingCapitalProjection(status="RESOLVED", years=[])
    ratios = FinancialRatioSet(years=[])
    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    assert val.failed_checks > 0
    assert val.all_passed is False


def test_freeze_K_validation_unresolved_yields_partially_derived():
    """K. Validation UNRESOLVED with no FAILED checks -> PARTIALLY_DERIVED / INSUFFICIENT_DATA."""
    su = FundingSourcesUses(status="INSUFFICIENT_DATA", total_sources=None, total_uses=None)
    bs = BalanceSheet(status="PARTIALLY_DERIVED", years=[BalanceSheetYear(year=1, total_assets=None, total_liabilities_and_equity=None, status="UNKNOWN")])
    cf = CashFlowStatement(status="PARTIALLY_DERIVED", years=[CashFlowYear(year=1, opening_cash_balance=None, closing_cash_balance=None, status="PARTIALLY_DERIVED")])
    pl = ProfitLossStatement(status="PARTIALLY_DERIVED", years=[ProfitLossYear(year=1, profit_after_tax=None)])
    wc = WorkingCapitalProjection(status="PARTIALLY_DERIVED", years=[])
    ratios = FinancialRatioSet(years=[])
    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    assert val.failed_checks == 0
    assert val.unresolved_checks > 0


def test_freeze_L_fully_specified_fixture_reconciles():
    """L. Fully specified fixture -> all required validation checks PASS and statements reconcile."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    fp = resp.financial_analysis.financial_projection
    assert fp.validation.all_passed is True
    assert fp.validation.failed_checks == 0
    assert fp.validation.unresolved_checks == 0
    assert resp.financial_analysis.balance_sheet.status == "BALANCED"
    assert resp.financial_analysis.cash_flow_statement.status == "RESOLVED"
    assert resp.financial_analysis.profit_loss_statement.status == "RESOLVED"


def test_freeze_M_stage9_loan_schedule_reconciles():
    """M. Existing Stage 9 loan schedule still reconciles."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    check_5 = next(c for c in resp.financial_analysis.financial_projection.validation.checks if c.check_id == "CHECK_5_STAGE9_LOAN_RECONCILIATION")
    assert check_5.status == "PASSED"
    assert check_5.difference <= 1.0


# =============================================================================
# MANDATORY TARGETED TESTS (1 THROUGH 23)
# =============================================================================

def test_part18_01_capex_known_depr_unknown_net_ppe_none():
    """TEST 1: CapEx known + depreciation unknown -> net PPE remains None -> no artificial zero depreciation."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=50000.0,
        term_loan=150000.0,
        capex=200000.0,
        opening_inventory=0.0,
        pre_operating_cost=0.0,
        contingency=0.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, closing_cash_balance=20000.0, principal_repayment=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, inventory=0.0, receivables=0.0, payables=0.0)])
    bs = balance_sheet_engine.generate(
        profit_loss=pl,
        cash_flow=cf,
        working_capital_proj=wc,
        sources_uses=su,
        depreciation_schedule={},  # Unknown depreciation
    )
    assert bs.years[0].gross_fixed_assets == 200000.0
    assert bs.years[0].accumulated_depreciation is None
    assert bs.years[0].net_fixed_assets is None
    assert bs.status == "PARTIALLY_DERIVED"


def test_part18_02_capex_known_depr_resolved_ppe_reconciles():
    """TEST 2: CapEx known + depreciation resolved -> PPE reconciles correctly."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=50000.0,
        term_loan=150000.0,
        capex=200000.0,
        opening_inventory=0.0,
        pre_operating_cost=0.0,
        contingency=0.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=50000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, closing_cash_balance=20000.0, principal_repayment=0.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, inventory=0.0, receivables=0.0, payables=0.0)])
    depr_sched = {
        1: DepreciationScheduleYear(
            year=1,
            gross_block=200000.0,
            depreciation_amount=20000.0,
            accumulated_depreciation=20000.0,
            net_block=180000.0,
            status="RESOLVED"
        )
    }
    bs = balance_sheet_engine.generate(
        profit_loss=pl,
        cash_flow=cf,
        working_capital_proj=wc,
        sources_uses=su,
        depreciation_schedule=depr_sched,
    )
    assert bs.years[0].gross_fixed_assets == 200000.0
    assert bs.years[0].accumulated_depreciation == 20000.0
    assert bs.years[0].net_fixed_assets == 180000.0


def test_part18_03_financial_ratios_complete_data_status_resolved():
    """TEST 3: Financial ratios with complete data -> status RESOLVED."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    ratios = resp.financial_analysis.financial_ratios
    assert ratios is not None
    assert ratios.status == "RESOLVED"


def test_part18_04_financial_ratios_missing_data_status_partially_derived():
    """TEST 4: Financial ratios with missing data -> status PARTIALLY_DERIVED / INSUFFICIENT_DATA."""
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, revenue=100000.0)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1)])
    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    assert ratios.status in ("PARTIALLY_DERIVED", "INSUFFICIENT_DATA")


def test_part18_05_missing_depreciation_does_not_become_zero_in_ratios():
    """TEST 5: Missing depreciation does not become zero in ratios."""
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, revenue=100000.0, profit_after_tax=20000.0, interest_expense=5000.0, depreciation=None)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, principal_repayment=10000.0)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1)])
    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    assert ratios.years[0].dscr is None


def test_part18_06_missing_principal_repayment_does_not_become_zero():
    """TEST 6: Missing principal repayment does not become zero."""
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, revenue=100000.0, profit_after_tax=20000.0, interest_expense=5000.0, depreciation=5000.0)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1, principal_repayment=None)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1)])
    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    assert ratios.years[0].dscr is None


def test_part18_07_debt_exists_no_schedule_principal_none_dscr_unresolved():
    """TEST 7: Debt + no Stage 9 schedule -> principal repayment None -> DSCR unresolved."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=50000.0,
        term_loan=200000.0,
        capex=150000.0,
        opening_inventory=50000.0,
        pre_operating_cost=0.0,
        contingency=0.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=20000.0, depreciation=10000.0, interest_expense=15000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    bs = BalanceSheet(years=[BalanceSheetYear(year=1, total_assets=250000.0, total_equity=50000.0, term_loan_outstanding=200000.0)])
    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=su,
        repayment_schedule=None,
    )
    assert cf.years[0].principal_repayment is None
    ratios = financial_ratios_engine.calculate(pl, bs, wc, cf)
    assert ratios.years[0].dscr is None


def test_part18_08_debt_zero_principal_repayment_zero():
    """TEST 8: Debt = 0 -> principal repayment = 0."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=200000.0,
        term_loan=0.0,
        capex=150000.0,
        opening_inventory=50000.0,
        pre_operating_cost=0.0,
        contingency=0.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=20000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(
        profit_loss=pl,
        working_capital_proj=wc,
        sources_uses=su,
        repayment_schedule=None,
    )
    assert cf.years[0].principal_repayment == 0.0


def test_part18_09_no_growth_evidence_default_year2_plus_unknown():
    """TEST 9: No growth evidence + default projection -> Year 2+ revenue UNKNOWN."""
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0}
    )
    assert rev_proj.years[0].revenue == 1200000.0
    assert rev_proj.years[1].revenue is None
    assert rev_proj.years[1].status == "UNKNOWN"
    assert rev_proj.years[1].growth_source == "UNKNOWN"


def test_part18_10_explicit_flat_growth_policy_provenance():
    """TEST 10: Explicit flat-growth policy -> Year 2+ revenue calculated -> provenance POLICY_SCENARIO."""
    rev_proj = revenue_projection_engine.project(
        projection_years=3,
        user_inputs={"monthly_revenue": 100000.0},
        allow_flat_base_case=True
    )
    assert rev_proj.years[1].revenue == 1200000.0
    assert rev_proj.years[1].growth_source == "POLICY_SCENARIO"
    assert rev_proj.years[1].growth_method == "EXPLICIT_FLAT_GROWTH_POLICY"


def test_part18_11_aggregate_project_cost_known_allocation_incomplete():
    """TEST 11: Aggregate project cost known but component allocation incomplete."""
    su = sources_uses_engine.build(
        total_project_cost=500000.0,
        user_inputs={"capex": 300000.0}
    )
    assert su.total_uses == 500000.0
    assert su.allocation_status == "PARTIALLY_ALLOCATED"
    assert su.opening_inventory is None
    assert su.pre_operating_cost is None


def test_part18_12_missing_year0_use_closing_cash_unresolved():
    """TEST 12: Missing Year-0 use -> Year-0 closing cash unresolved."""
    su = FundingSourcesUses(
        status="PARTIALLY_DERIVED",
        promoter_contribution=50000.0,
        term_loan=150000.0,
        capex=100000.0,
        opening_inventory=None,  # Missing
        pre_operating_cost=0.0,
        contingency=0.0
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=10000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(profit_loss=pl, working_capital_proj=wc, sources_uses=su)
    assert cf.year_0_deployment["closing_cash_balance"] is None


def test_part18_13_funding_shortfall_not_clamped_to_zero():
    """TEST 13: Funding shortfall is not clamped to zero."""
    su = FundingSourcesUses(
        status="RECONCILED",
        promoter_contribution=20000.0,
        term_loan=80000.0,  # Sources = 100,000
        capex=100000.0,
        opening_inventory=30000.0,
        pre_operating_cost=0.0,
        contingency=0.0   # Uses = 130,000
    )
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1, profit_after_tax=10000.0, depreciation=10000.0)])
    wc = WorkingCapitalProjection(years=[WorkingCapitalYear(year=1, change_in_working_capital=0.0)])
    cf = cash_flow_statement_engine.generate(profit_loss=pl, working_capital_proj=wc, sources_uses=su)
    assert cf.year_0_deployment["closing_cash_balance"] == -30000.0


def test_part18_14_missing_greenfield_flag_receivables_payables_unknown():
    """TEST 14: Missing greenfield flag -> opening receivables/payables remain UNKNOWN."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    wc = working_capital_projection_engine.project(
        revenue_projection=rev,
        cost_projection=None,
        user_inputs={}
    )
    assert wc.years[0].change_in_working_capital is None


def test_part18_15_is_greenfield_true_structural_zero_valid():
    """TEST 15: is_greenfield=True -> structural zero is valid."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0})
    wc = working_capital_projection_engine.project(
        revenue_projection=rev,
        cost_projection=None,
        user_inputs={"is_greenfield": True}
    )
    assert wc.status in ("RESOLVED", "PARTIALLY_DERIVED")


def test_part18_16_unknown_tax_pat_none():
    """TEST 16: Unknown tax -> PAT None."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0}, allow_flat_base_case=True)
    cost = cost_projection_engine.project(rev, user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0})
    pl = profit_loss_engine.generate(rev, cost, {}, user_inputs={})
    for y in pl.years:
        assert y.profit_after_tax is None
        assert y.tax_status == "NOT_MODELED"


def test_part18_17_explicit_zero_tax_pat_equals_pbt():
    """TEST 17: Explicit zero tax -> PAT = PBT."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0}, allow_flat_base_case=True)
    cost = cost_projection_engine.project(rev, user_inputs={"gross_margin": 40.0, "monthly_rent": 5000.0})
    pl = profit_loss_engine.generate(rev, cost, {}, tax_rate=0.0)
    for y in pl.years:
        assert y.profit_after_tax == y.profit_before_tax
        assert y.tax_expense == 0.0


def test_part18_18_unknown_opex_component_total_not_silently_reduced():
    """TEST 18: Unknown OPEX component -> total OPEX not silently reduced."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0}, allow_flat_base_case=True)
    cost = cost_projection_engine.project(
        revenue_projection=rev,
        user_inputs={"gross_margin": 40.0, "monthly_rent": 10000.0, "staff_count": 2}
    )
    for y in cost.years:
        assert y.salaries is None
        assert y.operating_expenses is None


def test_part18_19_validation_unresolved_data_unresolved_not_passed():
    """TEST 19: Validation unresolved data -> UNRESOLVED, not PASSED."""
    su = FundingSourcesUses(status="INSUFFICIENT_DATA", total_sources=None, total_uses=None)
    bs = BalanceSheet(years=[BalanceSheetYear(year=1)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1)])
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1)])
    wc = WorkingCapitalProjection(years=[])
    ratios = FinancialRatioSet(years=[])
    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    assert val.all_passed is False
    assert val.unresolved_checks > 0


def test_part18_20_actual_accounting_mismatch_failed_not_unresolved():
    """TEST 20: Actual accounting mismatch -> FAILED, not UNRESOLVED."""
    su = FundingSourcesUses(status="MISMATCH", total_sources=100000.0, total_uses=150000.0, promoter_contribution=10000.0, term_loan=90000.0)
    bs = BalanceSheet(years=[BalanceSheetYear(year=1)])
    cf = CashFlowStatement(years=[CashFlowYear(year=1)])
    pl = ProfitLossStatement(years=[ProfitLossYear(year=1)])
    wc = WorkingCapitalProjection(years=[])
    ratios = FinancialRatioSet(years=[])
    val = validation_engine.validate(su, bs, cf, pl, wc, ratios)
    check_1 = next(c for c in val.checks if c.check_id == "CHECK_1_SOURCES_USES")
    assert check_1.status == "FAILED"
    assert val.failed_checks > 0


def test_part18_21_fully_specified_end_to_end_fixture_reconciles():
    """TEST 21: Fully specified fixture produces reconciled statements and all 12 checks pass."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    fp = resp.financial_analysis.financial_projection
    assert fp.validation.all_passed is True
    assert fp.validation.failed_checks == 0
    assert fp.validation.unresolved_checks == 0
    assert resp.financial_analysis.balance_sheet.status == "BALANCED"
    assert resp.financial_analysis.cash_flow_statement.status == "RESOLVED"
    assert resp.financial_analysis.profit_loss_statement.status == "RESOLVED"
    assert resp.financial_analysis.financial_ratios.status == "RESOLVED"


def test_part18_22_stage9_loan_schedule_reconciles():
    """TEST 22: Stage 9 loan schedule reconciles within tolerance."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    check_5 = next(c for c in resp.financial_analysis.financial_projection.validation.checks if c.check_id == "CHECK_5_STAGE9_LOAN_RECONCILIATION")
    assert check_5.status == "PASSED"
    assert check_5.difference <= 1.0


def test_part18_23_m2_project_cost_wc_financing_propagation():
    """TEST 23: M2 project cost/WC/financing -> M3 sources & uses / Year-0 deployment correctly."""
    req = _build_retail_analysis_request(tax_rate=0.0)
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis
    assert fa.funding_sources_uses is not None
    assert fa.funding_sources_uses.capex == fa.project_cost_analysis.capex
    assert fa.funding_sources_uses.opening_inventory == fa.project_cost_analysis.opening_inventory
    assert fa.funding_sources_uses.working_capital_buffer == fa.project_cost_analysis.working_capital
    assert fa.cash_flow_statement.year_0_deployment["capex_outflow"] == fa.project_cost_analysis.capex
    assert fa.cash_flow_statement.year_0_deployment["opening_inventory_outflow"] == fa.project_cost_analysis.opening_inventory


def test_targeted_01_opex_unknown_propagation_salary_rent_known_elec_mkt_unknown():
    """Targeted Fix 1: salary + rent known, electricity/marketing unknown => total OPEX UNKNOWN."""
    rev = revenue_projection_engine.project(3, user_inputs={"monthly_revenue": 100000.0}, allow_flat_base_case=True)
    # Salary and rent are known, but electricity is unknown (None)
    cost_elec_unknown = cost_projection_engine.project(
        revenue_projection=rev,
        user_inputs={
            "gross_margin": 40.0,
            "monthly_rent": 10000.0,
            "monthly_salary": 20000.0,
            "electricity_cost": None,
        }
    )
    for y in cost_elec_unknown.years:
        assert y.salaries == 240000.0
        assert y.rent == 120000.0
        assert y.utilities_electricity is None
        assert y.total_operating_expenses is None
        assert y.status in ("INSUFFICIENT_DATA", "PARTIALLY_DERIVED")

    # Marketing unknown
    cost_mkt_unknown = cost_projection_engine.project(
        revenue_projection=rev,
        user_inputs={
            "gross_margin": 40.0,
            "monthly_rent": 10000.0,
            "monthly_salary": 20000.0,
            "electricity_cost": 2000.0,
            "marketing_cost": None,
        }
    )
    for y in cost_mkt_unknown.years:
        assert y.total_operating_expenses is None
        assert y.status in ("INSUFFICIENT_DATA", "PARTIALLY_DERIVED")


def test_targeted_02_zero_capex_missing_useful_life_resolved_zero_depreciation():
    """Targeted Fix 2: zero CapEx + missing useful life => resolved zero depreciation."""
    sched = depreciation_engine.calculate_schedule(
        projection_years=5,
        user_inputs={"capex": 0.0},
        useful_life_years=None,
        benchmark_data=None,
    )
    assert len(sched) == 5
    for y, line in sched.items():
        assert line.gross_block == 0.0
        assert line.depreciation_amount == 0.0
        assert line.accumulated_depreciation == 0.0
        assert line.net_block == 0.0
        assert line.status == "RESOLVED"


