"""
Milestone 4 Test Suite: Banking Appraisal & Viability Engine.
Covers all 22 required test cases:
1. Fully resolved business -> complete M4 appraisal
2. Missing revenue -> dependent metrics unresolved
3. Missing OPEX -> dependent metrics unresolved
4. Zero debt -> correct zero debt-service handling
5. Stage 9 DSCR matches -> reconciliation passes
6. Stage 9 DSCR mismatch -> validation/risk flag
7. Stage 9 interest mismatch -> validation/risk flag
8. Break-even reconciliation
9. Current/quick ratio with valid denominators
10. Zero denominator -> no crash / no fabricated ratio
11. DER + TOL/TNW
12. ROCE/ROE with valid inputs
13. IRR/NPV only with valid cash flows
14. Missing discount rate -> NPV unresolved
15. Promoter contribution gap
16. Financing gap
17. Missing net worth -> leverage metrics unresolved
18. Insufficient repayment capacity -> appropriate risk flag
19. Critical unresolved data -> NOT_ASSESSABLE
20. Provenance correctness
21. Validation tri-state correctness
22. M3 regression tests remain passing
"""
import pytest
from typing import Dict, Any, Optional

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    ProjectAssumptionsInput,
    ProfitLossStatement,
    BalanceSheet,
    CashFlowStatement,
    WorkingCapitalProjection,
    FundingSourcesUses,
    FinancialProjection,
    RevenueProjection,
    RevenueProjectionLine,
    CostProjection,
    CostProjectionLine,
    ProfitLossYear,
    BalanceSheetYear,
    CashFlowYear,
    LoanManagement,
    RepaymentSchedule,
    AmortizationRow,
    DebtServiceAnalysis,
    BreakEvenAnalysis,
    DSCRStatus,
    CalculationStatus,
    FinancialRatioSet,
    ProjectionValidation
)
from app.services.financial_engine.engine import financial_engine
from app.services.financial_engine.appraisal import (
    appraisal_engine,
    debt_service_engine,
    repayment_capacity_engine,
    dscr_analysis_engine,
    break_even_analysis_engine,
    liquidity_analysis_engine,
    profitability_analysis_engine,
    leverage_analysis_engine,
    banking_ratios_engine,
    promoter_contribution_engine,
    financing_structure_engine,
    risk_engine,
    viability_engine,
    appraisal_validation_engine,
    appraisal_summary_builder,
    DebtServiceAnalysisResult,
    RepaymentCapacityResult,
    ProfitabilityAnalysisResult,
    FinancingStructureResult,
    PromoterContributionResult,
    AppraisalStatus,
    ViabilityClassification,
    ValidationState,
    RiskSeverity,
    ReasonCode,
    MetricSource
)
from app.services.financial_engine.appraisal.constants import (
    LIQUIDITY_CURRENT_RATIO_ADEQUATE,
    LIQUIDITY_CURRENT_RATIO_TIGHT
)


def _build_retail_analysis_request(tax_rate: Optional[float] = 0.0, discount_rate: Optional[float] = 0.12) -> FinancialAnalysisRequest:
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
    if discount_rate is not None:
        inputs["discount_rate"] = discount_rate

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
# 1. Fully Resolved Business -> Complete M4 Appraisal
# =============================================================================
def test_01_fully_resolved_business_appraisal():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    m4 = resp.financial_analysis.banking_appraisal

    assert m4 is not None
    assert m4.status in (AppraisalStatus.RESOLVED, AppraisalStatus.PARTIALLY_DERIVED)
    assert m4.appraisal is not None
    assert m4.appraisal.project_cost is not None and m4.appraisal.project_cost > 0
    assert m4.appraisal.promoter_contribution is not None
    assert m4.appraisal.debt_exposure is not None
    assert m4.appraisal.average_dscr is not None and m4.appraisal.average_dscr > 0
    assert m4.viability.classification in (ViabilityClassification.FINANCIALLY_VIABLE, ViabilityClassification.CONDITIONALLY_VIABLE)
    assert len(m4.provenance) > 0


# =============================================================================
# 2. Missing Revenue -> Dependent Metrics Unresolved
# =============================================================================
def test_02_missing_revenue_unresolved():
    # Construct projection with missing revenue
    rev_proj = RevenueProjection(
        status="INSUFFICIENT_DATA",
        years=[RevenueProjectionLine(year=1, revenue=None)]
    )
    cost_proj = CostProjection(status="RESOLVED", years=[CostProjectionLine(year=1, cogs=100000.0, total_operating_expenses=50000.0)])
    pl_stmt = ProfitLossStatement(status="UNRESOLVED", years=[ProfitLossYear(year=1, revenue=None, cogs=100000.0, gross_profit=None)])

    fin_proj = FinancialProjection(
        status="INSUFFICIENT_DATA",
        projection_years=1,
        revenue_projection=rev_proj,
        cost_projection=cost_proj,
        profit_loss_statement=pl_stmt,
        cash_flow_statement=CashFlowStatement(years=[]),
        balance_sheet=BalanceSheet(years=[]),
        working_capital_projection=WorkingCapitalProjection(years=[]),
        financial_ratios=FinancialRatioSet(),
        funding_sources_uses=FundingSourcesUses(total_uses=200000.0, total_sources=200000.0),
        validation=ProjectionValidation(),
    )

    res = appraisal_engine.appraise(financial_projection=fin_proj)
    assert "revenue" in res.critical_unknowns
    assert res.profitability.years[0].gross_margin_pct is None
    assert res.profitability.years[0].reason_code == ReasonCode.MISSING_REVENUE
    assert res.viability.classification == ViabilityClassification.NOT_ASSESSABLE


# =============================================================================
# 3. Missing OPEX -> Dependent Metrics Unresolved
# =============================================================================
def test_03_missing_opex_unresolved():
    rev_proj = RevenueProjection(status="RESOLVED", years=[RevenueProjectionLine(year=1, revenue=500000.0)])
    cost_proj = CostProjection(status="INSUFFICIENT_DATA", years=[CostProjectionLine(year=1, total_operating_expenses=None)])
    pl_stmt = ProfitLossStatement(status="UNRESOLVED", years=[ProfitLossYear(year=1, revenue=500000.0, cogs=300000.0, operating_expenses=None, ebitda=None, profit_after_tax=None)])

    fin_proj = FinancialProjection(
        status="INSUFFICIENT_DATA",
        projection_years=1,
        revenue_projection=rev_proj,
        cost_projection=cost_proj,
        profit_loss_statement=pl_stmt,
        cash_flow_statement=CashFlowStatement(years=[]),
        balance_sheet=BalanceSheet(years=[]),
        working_capital_projection=WorkingCapitalProjection(years=[]),
        financial_ratios=FinancialRatioSet(),
        funding_sources_uses=FundingSourcesUses(total_uses=200000.0, total_sources=200000.0),
        validation=ProjectionValidation(),
    )

    res = appraisal_engine.appraise(financial_projection=fin_proj)
    assert "operating_expenses" in res.critical_unknowns
    assert res.dscr.average_dscr is None
    assert res.viability.classification == ViabilityClassification.NOT_ASSESSABLE


# =============================================================================
# 4. Zero Debt -> Correct Zero Debt-Service Handling
# =============================================================================
def test_04_zero_debt_handling():
    loan_mgmt = LoanManagement(
        principal=0.0,
        annual_interest_rate=0.0,
        monthly_interest_rate=0.0,
        tenure_months=60,
        monthly_emi=0.0,
        total_interest=0.0,
        total_repayment=0.0
    )
    pl_stmt = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=250000.0, gross_profit=250000.0, operating_expenses=100000.0, ebitda=150000.0, ebit=150000.0, depreciation=0.0, interest_expense=0.0, profit_after_tax=150000.0)
    ])

    ds = debt_service_engine.evaluate(projection_years=1, loan_management=loan_mgmt)
    assert ds.is_zero_debt is True
    assert ds.total_debt_service == 0.0
    assert ds.years[0].total_debt_service == 0.0
    assert ds.reason_code == ReasonCode.ZERO_DEBT

    rc = repayment_capacity_engine.evaluate(debt_service=ds, profit_loss=pl_stmt)
    assert rc.capacity_assessment == "STRONG_ZERO_DEBT"

    dscr_res = dscr_analysis_engine.evaluate(repayment_capacity=rc, debt_service=ds)
    assert dscr_res.average_dscr is None
    assert dscr_res.minimum_dscr is None
    assert dscr_res.status == AppraisalStatus.NOT_APPLICABLE
    assert dscr_res.reason_code == ReasonCode.ZERO_DEBT


# =============================================================================
# 5. Stage 9 DSCR Matches -> Reconciliation Passes
# =============================================================================
def test_05_stage9_dscr_match_reconciliation():
    st9_ds = DebtServiceAnalysis(dscr=1.85, status=DSCRStatus.STRONG)

    pl_stmt = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=250000.0, gross_profit=250000.0, operating_expenses=100000.0, ebitda=150000.0, ebit=130000.0, depreciation=20000.0, interest_expense=15000.0, profit_after_tax=100000.0)
    ])
    # CADS = 100000 + 20000 + 15000 = 135000. Debt service = 72972 -> DSCR = 1.85
    ds_res = debt_service_engine.evaluate(
        projection_years=1,
        repayment_schedule=RepaymentSchedule(monthly_schedule=[
            AmortizationRow(period=m, phase="REPAYMENT", opening_balance=400000.0, payment=6081.0, principal_component=4831.0, interest_component=1250.0, closing_balance=395000.0)
            for m in range(1, 13)
        ])
    )
    rc_res = repayment_capacity_engine.evaluate(debt_service=ds_res, profit_loss=pl_stmt)
    dscr_res = dscr_analysis_engine.evaluate(repayment_capacity=rc_res, debt_service=ds_res, stage9_debt_service=st9_ds)

    assert dscr_res.reconciliation_status == ValidationState.PASSED
    assert dscr_res.stage9_dscr == 1.85


# =============================================================================
# 6. Stage 9 DSCR Mismatch -> Validation/Risk Flag
# =============================================================================
def test_06_stage9_dscr_mismatch_flag():
    # Stage 9 expects 3.50, but M4 calculates ~1.85
    st9_ds = DebtServiceAnalysis(dscr=3.50, status=DSCRStatus.STRONG)

    pl_stmt = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=250000.0, gross_profit=250000.0, operating_expenses=100000.0, ebitda=150000.0, ebit=130000.0, depreciation=20000.0, interest_expense=15000.0, profit_after_tax=100000.0)
    ])
    ds_res = debt_service_engine.evaluate(
        projection_years=1,
        repayment_schedule=RepaymentSchedule(monthly_schedule=[
            AmortizationRow(period=m, phase="REPAYMENT", opening_balance=400000.0, payment=6081.0, principal_component=4831.0, interest_component=1250.0, closing_balance=395000.0)
            for m in range(1, 13)
        ])
    )
    rc_res = repayment_capacity_engine.evaluate(debt_service=ds_res, profit_loss=pl_stmt)
    dscr_res = dscr_analysis_engine.evaluate(repayment_capacity=rc_res, debt_service=ds_res, stage9_debt_service=st9_ds, tolerance=0.10)

    assert dscr_res.reconciliation_status == ValidationState.FAILED
    assert dscr_res.reason_code == ReasonCode.STAGE9_RECONCILIATION_FAILED

    # Check risk engine catches it
    risk_res = risk_engine.evaluate(dscr=dscr_res)
    recon_flags = [f for f in risk_res.flags if f.reason_code == ReasonCode.STAGE9_RECONCILIATION_FAILED]
    assert len(recon_flags) == 1
    assert recon_flags[0].severity == RiskSeverity.HIGH


# =============================================================================
# 7. Stage 9 Interest Mismatch -> Validation/Risk Flag
# =============================================================================
def test_07_stage9_interest_mismatch_flag():
    # Loan management expects 50,000 total interest, but schedule sums to 15,000
    loan_mgmt = LoanManagement(
        principal=300000.0,
        annual_interest_rate=0.10,
        monthly_interest_rate=0.10 / 12,
        tenure_months=12,
        monthly_emi=26375.0,
        total_interest=50000.0,  # deliberately inflated
        total_repayment=350000.0
    )
    ds_res = debt_service_engine.evaluate(
        projection_years=1,
        repayment_schedule=RepaymentSchedule(monthly_schedule=[
            AmortizationRow(period=m, phase="REPAYMENT", opening_balance=300000.0, payment=26375.0, principal_component=25000.0, interest_component=1250.0, closing_balance=275000.0)
            for m in range(1, 13)
        ])
    )
    val_res = appraisal_validation_engine.validate(loan_management=loan_mgmt, debt_service=ds_res)
    int_check = next((c for c in val_res.checks if c.check_id == "VAL_STAGE9_INTEREST_RECONCILIATION"), None)
    assert int_check is not None
    assert int_check.status == ValidationState.FAILED
    assert int_check.reason_code == ReasonCode.STAGE9_INTEREST_MISMATCH


# =============================================================================
# 8. Break-Even Reconciliation
# =============================================================================
def test_08_break_even_reconciliation():
    pl_stmt = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=600000.0, cogs=300000.0, operating_expenses=120000.0, depreciation=0.0)
    ])
    # Contribution = 600k - 300k = 300k. CMR = 0.50. Fixed costs = 120k * 1.0 = 120k.
    # Break even sales = 120k / 0.50 = 240,000. Utilization = 40.0%.
    st9_be = BreakEvenAnalysis(status=CalculationStatus.CALCULATED, annual_break_even_revenue=240000.0, break_even_utilization_pct=40.0)

    be_res = break_even_analysis_engine.evaluate(profit_loss=pl_stmt, stage9_break_even=st9_be, fixed_cost_ratio=1.0)
    assert be_res.year1_break_even_sales == 240000.0
    assert be_res.year1_break_even_utilization_pct == 40.0
    assert be_res.year1_margin_of_safety_pct == 60.0
    assert be_res.reconciliation_status == ValidationState.PASSED


# =============================================================================
# 9. Current/Quick Ratio with Valid Denominators
# =============================================================================
def test_09_current_quick_ratio_valid():
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=150000.0, inventory=50000.0, trade_payables=40000.0, other_current_liabilities=35000.0, cash_and_bank=25000.0)
    ])
    # CL = 40000 + 35000 = 75000.
    # CR = 150000 / 75000 = 2.0.
    # QR = (150000 - 50000) / 75000 = 1.33.
    liq = liquidity_analysis_engine.evaluate(balance_sheet=bs)
    assert liq.years[0].current_ratio == 2.0
    assert liq.years[0].quick_ratio == 1.33
    assert liq.average_current_ratio == 2.0
    assert liq.working_capital_adequacy == "ADEQUATE"


# =============================================================================
# 10. Zero Denominator -> No Crash / No Fabricated Ratio
# =============================================================================
def test_10_zero_denominator_no_crash():
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=100000.0, inventory=0.0, trade_payables=0.0, other_current_liabilities=0.0)
    ])
    # CL == 0.0 -> Should return None with ZERO_DENOMINATOR, not crash or return Inf
    liq = liquidity_analysis_engine.evaluate(balance_sheet=bs)
    assert liq.years[0].current_ratio is None
    assert liq.years[0].reason_code == ReasonCode.ZERO_DENOMINATOR


# =============================================================================
# 11. DER + TOL/TNW
# =============================================================================
def test_11_der_and_tol_tnw():
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, term_loan_outstanding=300000.0, total_equity=150000.0, trade_payables=30000.0, other_current_liabilities=20000.0, total_assets=500000.0)
    ])
    # DER = 300,000 / 150,000 = 2.0
    # TOL = 300,000 + 50,000 = 350,000. TOL/TNW = 350,000 / 150,000 = 2.33
    lev = leverage_analysis_engine.evaluate(balance_sheet=bs)
    assert lev.initial_der == 2.0
    assert lev.initial_tol_tnw == 2.33
    assert lev.years[0].debt_to_assets_ratio == 0.60


# =============================================================================
# 12. ROCE/ROE with Valid Inputs
# =============================================================================
def test_12_roce_and_roe_valid():
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=1000000.0, gross_profit=400000.0, ebitda=200000.0, ebit=150000.0, profit_after_tax=100000.0)
    ])
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_equity=200000.0, term_loan_outstanding=300000.0, total_assets=600000.0)
    ])
    # Capital employed = 200k + 300k = 500k. ROCE = (150k / 500k) * 100 = 30.0%
    # ROE = (100k / 200k) * 100 = 50.0%
    # ROA = (100k / 600k) * 100 = 16.67%
    prof = profitability_analysis_engine.evaluate(profit_loss=pl, balance_sheet=bs)
    assert prof.years[0].roce_pct == 30.0
    assert prof.years[0].roe_pct == 50.0
    assert prof.years[0].roa_pct == 16.67


# =============================================================================
# 13. IRR/NPV Only with Valid Cash Flows
# =============================================================================
def test_13_irr_npv_valid_cash_flows():
    sources_uses = FundingSourcesUses(total_uses=300000.0, total_sources=300000.0)
    cf = CashFlowStatement(years=[
        CashFlowYear(year=1, cash_from_operations=100000.0),
        CashFlowYear(year=2, cash_from_operations=120000.0),
        CashFlowYear(year=3, cash_from_operations=140000.0),
        CashFlowYear(year=4, cash_from_operations=160000.0),
        CashFlowYear(year=5, cash_from_operations=180000.0),
    ])
    br = banking_ratios_engine.evaluate(cash_flow=cf, sources_uses=sources_uses, discount_rate=0.10)
    assert br.irr is not None and br.irr > 0.0
    assert br.npv is not None and br.npv > 0.0
    assert br.payback_period_years is not None and 2.0 <= br.payback_period_years <= 3.0


# =============================================================================
# 14. Missing Discount Rate -> NPV Unresolved
# =============================================================================
def test_14_missing_discount_rate_npv_unresolved():
    sources_uses = FundingSourcesUses(total_uses=300000.0, total_sources=300000.0)
    cf = CashFlowStatement(years=[
        CashFlowYear(year=1, cash_from_operations=100000.0),
        CashFlowYear(year=2, cash_from_operations=120000.0),
    ])
    # discount_rate=None -> NPV must NOT fabricate a rate
    br = banking_ratios_engine.evaluate(cash_flow=cf, sources_uses=sources_uses, discount_rate=None)
    assert br.npv is None


# =============================================================================
# 15. Promoter Contribution Gap
# =============================================================================
def test_15_promoter_contribution_gap():
    # Total cost = 500,000. Required margin 15% = 75,000. Actual = 50,000. Deficit = 25,000.
    sources_uses = FundingSourcesUses(total_uses=500000.0, promoter_contribution=50000.0, term_loan=450000.0, total_sources=500000.0)
    prom = promoter_contribution_engine.evaluate(sources_uses=sources_uses, scheme_margin_ratio=0.15)

    assert prom.is_adequate is False
    assert prom.gap_surplus == -25000.0
    assert prom.reason_code == ReasonCode.PROMOTER_CONTRIBUTION_GAP

    risk_res = risk_engine.evaluate(promoter_contribution=prom)
    flag = next((f for f in risk_res.flags if f.reason_code == ReasonCode.PROMOTER_CONTRIBUTION_GAP), None)
    assert flag is not None
    assert flag.severity == RiskSeverity.HIGH


# =============================================================================
# 16. Financing Gap
# =============================================================================
def test_16_financing_gap():
    # Uses = 500,000. Sources = 400,000. Deficit = -100,000
    sources_uses = FundingSourcesUses(total_uses=500000.0, promoter_contribution=100000.0, term_loan=300000.0, total_sources=400000.0)
    fin = financing_structure_engine.evaluate(sources_uses=sources_uses)

    assert fin.is_balanced is False
    assert fin.financing_gap_surplus == -100000.0
    assert fin.reason_code == ReasonCode.FINANCING_GAP

    risk_res = risk_engine.evaluate(financing=fin)
    flag = next((f for f in risk_res.flags if f.reason_code == ReasonCode.FINANCING_GAP), None)
    assert flag is not None
    assert flag.severity == RiskSeverity.CRITICAL


# =============================================================================
# 17. Missing Net Worth -> Leverage Metrics Unresolved
# =============================================================================
def test_17_missing_net_worth_leverage_unresolved():
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, term_loan_outstanding=300000.0, total_equity=None)
    ])
    lev = leverage_analysis_engine.evaluate(balance_sheet=bs)
    assert lev.initial_der is None
    assert lev.years[0].reason_code == ReasonCode.MISSING_NET_WORTH


# =============================================================================
# 18. Insufficient Repayment Capacity -> Appropriate Risk Flag
# =============================================================================
def test_18_insufficient_repayment_capacity():
    # CADS = 40,000, Debt service = 60,000
    ds = DebtServiceAnalysisResult(
        status=AppraisalStatus.RESOLVED,
        years=[],
        total_debt_service=60000.0,
        is_zero_debt=False
    )
    ds.years.append(type("DSY", (), {"year": 1, "total_debt_service": 60000.0})())

    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, profit_after_tax=30000.0, depreciation=5000.0, interest_expense=5000.0)
    ])
    rc = repayment_capacity_engine.evaluate(debt_service=ds, profit_loss=pl)
    assert rc.capacity_assessment == "INSUFFICIENT"

    risk_res = risk_engine.evaluate(repayment_capacity=rc)
    flag = next((f for f in risk_res.flags if f.reason_code == ReasonCode.WEAK_REPAYMENT_CAPACITY), None)
    assert flag is not None
    assert flag.severity == RiskSeverity.CRITICAL


# =============================================================================
# 19. Critical Unresolved Data -> NOT_ASSESSABLE
# =============================================================================
def test_19_critical_unresolved_not_assessable():
    viab = viability_engine.evaluate(
        risk_result=risk_engine.evaluate(),
        critical_unknowns=["revenue", "operating_expenses"]
    )
    assert viab.classification == ViabilityClassification.NOT_ASSESSABLE
    assert ReasonCode.INSUFFICIENT_DATA in viab.reason_codes
    assert "revenue" in viab.unresolved_dependencies


# =============================================================================
# 20. Provenance Correctness
# =============================================================================
def test_20_provenance_correctness():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    m4 = resp.financial_analysis.banking_appraisal

    assert len(m4.provenance) > 0
    for p in m4.provenance:
        assert p.source in (MetricSource.USER, MetricSource.STAGE9, MetricSource.M1, MetricSource.M2, MetricSource.M3, MetricSource.DERIVED, MetricSource.BENCHMARK, MetricSource.SCHEME)
        if p.calculation_method is not None:
            # Derived metrics cannot be marked as pure USER input
            assert p.source != MetricSource.USER


# =============================================================================
# 21. Validation Tri-State Correctness
# =============================================================================
def test_21_validation_tristate_correctness():
    val = appraisal_validation_engine.validate(critical_unknowns=["revenue"])
    assert val.all_passed is False
    assert val.unresolved_checks > 0
    # all_passed must be True ONLY when failed == 0 and unresolved == 0
    for c in val.checks:
        assert c.status in (ValidationState.PASSED, ValidationState.FAILED, ValidationState.UNRESOLVED)


# =============================================================================
# 22. M3 Regression Tests Remain Passing
# =============================================================================
def test_22_m3_regression_tests_pass():
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    fa = resp.financial_analysis

    # Verify M1/M2/M3 still present and functional
    assert fa.financial_projection is not None
    assert fa.profit_loss_statement is not None
    assert fa.balance_sheet is not None
    assert fa.cash_flow_statement is not None
    assert fa.banking_appraisal is not None
    assert resp.workflow.state == "FINANCIAL_VIABILITY_EVALUATED"


# =============================================================================
# TARGETED HARDENING TESTS (BLOCKERS 1-6 & VERIFICATION)
# =============================================================================

def test_h01_missing_fixed_variable_split_break_even_unresolved():
    """1. Missing fixed/variable cost split -> break-even unresolved with INSUFFICIENT_DATA."""
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=250000.0, operating_expenses=100000.0)
    ])
    be = break_even_analysis_engine.evaluate(profit_loss=pl, fixed_cost_ratio=None)
    assert be.status == AppraisalStatus.UNRESOLVED
    assert be.year1_break_even_sales is None
    assert be.year1_break_even_utilization_pct is None
    assert be.year1_margin_of_safety_pct is None
    assert be.reason_code == ReasonCode.INSUFFICIENT_DATA


def test_h02_missing_scheme_margin_promoter_unresolved():
    """2. Missing scheme/user margin -> promoter requirement unresolved."""
    sources_uses = FundingSourcesUses(total_uses=500000.0, promoter_contribution=50000.0)
    prom = promoter_contribution_engine.evaluate(sources_uses=sources_uses, project_financing=None, scheme_margin_ratio=None)
    assert prom.status == AppraisalStatus.UNRESOLVED
    assert prom.required_promoter_contribution is None
    assert prom.gap_surplus is None
    assert prom.reason_code == ReasonCode.INSUFFICIENT_DATA


def test_h03_explicit_zero_debt_dscr_na_never_10x():
    """3. Explicit zero debt -> DSCR N/A, never 10.0x ceiling."""
    loan_mgmt = LoanManagement(principal=0.0, annual_interest_rate=0.0, monthly_interest_rate=0.0, tenure_months=60, monthly_emi=0.0, total_interest=0.0, total_repayment=0.0)
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=250000.0, gross_profit=250000.0, operating_expenses=100000.0, ebitda=150000.0, ebit=150000.0, depreciation=0.0, interest_expense=0.0, profit_after_tax=150000.0)
    ])
    ds = debt_service_engine.evaluate(projection_years=1, loan_management=loan_mgmt)
    rc = repayment_capacity_engine.evaluate(debt_service=ds, profit_loss=pl)
    dscr = dscr_analysis_engine.evaluate(repayment_capacity=rc, debt_service=ds)

    assert dscr.average_dscr is None
    assert dscr.minimum_dscr is None
    assert dscr.average_dscr != 10.0
    assert dscr.status == AppraisalStatus.NOT_APPLICABLE
    assert dscr.reason_code == ReasonCode.ZERO_DEBT


def test_h04_missing_repayment_input_no_zero_substitution():
    """4. Missing repayment input -> no zero substitution; derived metrics unresolved."""
    ds = DebtServiceAnalysisResult(status=AppraisalStatus.RESOLVED, years=[], total_debt_service=50000.0, is_zero_debt=False)
    ds.years.append(type("DSY", (), {"year": 1, "total_debt_service": 50000.0})())

    # ProfitLoss with depreciation=None (missing input)
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, profit_after_tax=100000.0, depreciation=None, interest_expense=10000.0)
    ])
    rc = repayment_capacity_engine.evaluate(debt_service=ds, profit_loss=pl)
    assert rc.status == AppraisalStatus.UNRESOLVED
    assert rc.total_cads is None
    assert rc.cumulative_surplus_deficit is None
    assert rc.years[0].cash_available_for_debt_service is None
    assert rc.reason_code == ReasonCode.INSUFFICIENT_DATA


def test_h05_missing_liquidity_input_no_zero_substitution():
    """5. Missing liquidity input -> no zero substitution."""
    # BalanceSheet with trade_payables=None
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=200000.0, trade_payables=None, other_current_liabilities=None)
    ])
    liq = liquidity_analysis_engine.evaluate(balance_sheet=bs)
    assert liq.years[0].current_liabilities is None
    assert liq.years[0].current_ratio is None
    assert liq.status == AppraisalStatus.UNRESOLVED
    assert liq.working_capital_adequacy == "UNRESOLVED"


def test_h06_missing_financing_component_no_fabricated_source():
    """6. Missing financing component -> no fabricated source."""
    sources_uses = FundingSourcesUses(total_uses=500000.0, promoter_contribution=None, term_loan=350000.0)
    fin = financing_structure_engine.evaluate(sources_uses=sources_uses)
    assert fin.status == AppraisalStatus.UNRESOLVED
    assert fin.unresolved_component == "promoter_contribution"
    assert fin.financing_gap_surplus is None
    assert fin.reason_code == ReasonCode.INSUFFICIENT_DATA


def test_h07_critical_unresolved_appraisal_not_assessable():
    """7. Critical unresolved appraisal -> NOT_ASSESSABLE."""
    viab = viability_engine.evaluate(
        risk_result=risk_engine.evaluate(),
        critical_unknowns=["project_cost"]
    )
    assert viab.classification == ViabilityClassification.NOT_ASSESSABLE
    assert ReasonCode.INSUFFICIENT_DATA in viab.reason_codes
    assert "project_cost" in viab.unresolved_dependencies


def test_h08_fully_resolved_appraisal_normal_viability():
    """8. Fully resolved appraisal -> normal viability path."""
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    m4 = resp.financial_analysis.banking_appraisal
    assert m4 is not None
    assert m4.viability.classification == ViabilityClassification.FINANCIALLY_VIABLE
    assert len(m4.viability.unresolved_dependencies) == 0


def test_h09_missing_discount_rate_npv_unresolved():
    """9. Missing discount rate -> NPV unresolved with MISSING_DISCOUNT_RATE."""
    sources_uses = FundingSourcesUses(total_uses=200000.0, total_sources=200000.0)
    cf = CashFlowStatement(years=[
        CashFlowYear(year=1, cash_from_operations=80000.0),
        CashFlowYear(year=2, cash_from_operations=90000.0),
        CashFlowYear(year=3, cash_from_operations=100000.0),
    ])
    br = banking_ratios_engine.evaluate(cash_flow=cf, sources_uses=sources_uses, discount_rate=None)
    assert br.npv is None
    assert br.reason_code == ReasonCode.MISSING_DISCOUNT_RATE
    # IRR should still be calculated
    assert br.irr is not None and br.irr > 0.0


def test_h10_complete_cash_flow_series_deterministic_irr_payback():
    """10. Complete cash-flow series -> deterministic IRR and payback."""
    sources_uses = FundingSourcesUses(total_uses=200000.0, total_sources=200000.0)
    cf = CashFlowStatement(years=[
        CashFlowYear(year=1, cash_from_operations=70000.0),
        CashFlowYear(year=2, cash_from_operations=80000.0),
        CashFlowYear(year=3, cash_from_operations=90000.0),
        CashFlowYear(year=4, cash_from_operations=100000.0),
        CashFlowYear(year=5, cash_from_operations=110000.0),
    ])
    br = banking_ratios_engine.evaluate(cash_flow=cf, sources_uses=sources_uses, discount_rate=0.10)
    assert br.irr is not None and 20.0 < br.irr < 35.0
    assert br.payback_period_years is not None and 2.0 < br.payback_period_years < 3.0
    assert br.npv is not None and br.npv > 0.0


def test_h11_liquidity_threshold_consistency():
    """11. Liquidity threshold consistency: no contradictory ADEQUATE classifications."""
    assert LIQUIDITY_CURRENT_RATIO_ADEQUATE == 1.33
    assert LIQUIDITY_CURRENT_RATIO_TIGHT == 1.00

    # Test an enterprise with current ratio = 1.20 (below 1.33, above 1.0)
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=120000.0, trade_payables=100000.0, other_current_liabilities=0.0)
    ])
    liq = liquidity_analysis_engine.evaluate(balance_sheet=bs)
    assert liq.average_current_ratio == 1.20
    assert liq.working_capital_adequacy == "TIGHT"  # Not ADEQUATE!

    # Summary builder must also mark it TIGHT, not ADEQUATE
    summary = appraisal_summary_builder.build(liquidity=liq)
    assert summary.liquidity_position == "TIGHT"  # Not ADEQUATE!

    # Viability engine must mark it CONDITIONALLY_VIABLE due to WEAK_LIQUIDITY
    risk_res = risk_engine.evaluate(liquidity=liq)
    viab = viability_engine.evaluate(
        risk_result=risk_res,
        debt_service=DebtServiceAnalysisResult(is_zero_debt=True, status=AppraisalStatus.RESOLVED),
        repayment_capacity=RepaymentCapacityResult(capacity_assessment="ROBUST", status=AppraisalStatus.RESOLVED),
        profitability=ProfitabilityAnalysisResult(status=AppraisalStatus.RESOLVED, average_net_profit_margin_pct=15.0),
        financing=FinancingStructureResult(status=AppraisalStatus.RESOLVED, is_balanced=True, total_sources=100000.0, total_uses=100000.0),
        promoter_contribution=PromoterContributionResult(status=AppraisalStatus.RESOLVED, is_adequate=True),
        liquidity=liq
    )
    assert viab.classification == ViabilityClassification.CONDITIONALLY_VIABLE
    assert ReasonCode.WEAK_LIQUIDITY in viab.reason_codes


def test_h12_existing_stage9_reconciliation_integrity():
    """12. Existing Stage 9 reconciliation and regression tests still pass completely."""
    req = _build_retail_analysis_request()
    resp = financial_engine.analyze(req)
    m4 = resp.financial_analysis.banking_appraisal
    val = m4.validation

    assert val.all_passed is True
    assert val.failed_checks == 0
    assert val.unresolved_checks == 0
    assert m4.dscr.reconciliation_status == ValidationState.PASSED
    assert m4.break_even.reconciliation_status == ValidationState.PASSED


# =============================================================================
# Targeted Tests 1-7 (M4 Final Patch Verification)
# =============================================================================

def test_targeted_01_benchmark_fixed_cost_ratio_reaches_m4_break_even():
    """1. Benchmark fixed_cost_ratio reaches M4 break-even engine."""
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=200000.0, operating_expenses=100000.0)
    ])
    fp = FinancialProjection.model_construct(profit_loss_statement=pl)
    
    # Via benchmark_data dict
    appraisal_dict = appraisal_engine.appraise(
        financial_projection=fp,
        benchmark_data={"fixed_cost_ratio": 0.40}
    )
    assert appraisal_dict.break_even.status == AppraisalStatus.RESOLVED
    assert appraisal_dict.break_even.years[0].fixed_costs == 40000.0
    assert appraisal_dict.break_even.year1_break_even_sales is not None

    # Via benchmark_data object
    class BenchmarkObj:
        fixed_cost_ratio = 0.30
    appraisal_obj = appraisal_engine.appraise(
        financial_projection=fp,
        benchmark_data=BenchmarkObj()
    )
    assert appraisal_obj.break_even.status == AppraisalStatus.RESOLVED
    assert appraisal_obj.break_even.years[0].fixed_costs == 30000.0


def test_targeted_02_missing_fixed_cost_ratio_break_even_unresolved():
    """2. Missing fixed_cost_ratio -> break-even UNRESOLVED."""
    pl = ProfitLossStatement(years=[
        ProfitLossYear(year=1, revenue=500000.0, cogs=200000.0, operating_expenses=100000.0)
    ])
    fp = FinancialProjection.model_construct(profit_loss_statement=pl)
    appraisal = appraisal_engine.appraise(
        financial_projection=fp,
        fixed_cost_ratio=None,
        benchmark_data=None
    )
    assert appraisal.break_even.status == AppraisalStatus.UNRESOLVED
    assert appraisal.break_even.year1_break_even_sales is None
    assert appraisal.break_even.reason_code == ReasonCode.INSUFFICIENT_DATA


def test_targeted_03_missing_other_current_liabilities_liquidity_unresolved():
    """3. Missing other_current_liabilities -> liquidity current ratio UNRESOLVED."""
    bs = BalanceSheet(years=[
        BalanceSheetYear(year=1, total_current_assets=150000.0, trade_payables=100000.0, other_current_liabilities=None)
    ])
    liq = liquidity_analysis_engine.evaluate(balance_sheet=bs)
    assert liq.years[0].current_liabilities is None
    assert liq.years[0].current_ratio is None
    assert liq.average_current_ratio is None
    assert liq.working_capital_adequacy == "UNRESOLVED"


def test_targeted_04_missing_other_current_liabilities_leverage_unresolved():
    """4. Same condition -> leverage liabilities/ratios unresolved."""
    bs = BalanceSheet(years=[
        BalanceSheetYear(
            year=1,
            total_current_assets=150000.0,
            trade_payables=100000.0,
            other_current_liabilities=None,
            term_loan_outstanding=200000.0,
            total_equity=100000.0,
            total_assets=350000.0
        )
    ])
    lev = leverage_analysis_engine.evaluate(balance_sheet=bs)
    assert lev.years[0].total_outside_liabilities is None
    assert lev.years[0].tol_tnw_ratio is None
    assert lev.initial_tol_tnw is None


def test_targeted_05_missing_discount_rate_npv_none_partially_derived():
    """5. Missing discount rate -> NPV None + PARTIALLY_DERIVED when IRR/payback resolve."""
    sources_uses = FundingSourcesUses(total_uses=200000.0, total_sources=200000.0)
    cf = CashFlowStatement(years=[
        CashFlowYear(year=1, cash_from_operations=80000.0),
        CashFlowYear(year=2, cash_from_operations=90000.0),
        CashFlowYear(year=3, cash_from_operations=100000.0),
    ])
    br = banking_ratios_engine.evaluate(cash_flow=cf, sources_uses=sources_uses, discount_rate=None)
    assert br.npv is None
    assert br.reason_code == ReasonCode.MISSING_DISCOUNT_RATE
    assert br.irr is not None and br.irr > 0.0
    assert br.payback_period_years is not None
    assert br.return_metrics_status == AppraisalStatus.PARTIALLY_DERIVED
    assert br.status == AppraisalStatus.PARTIALLY_DERIVED


def test_targeted_06_missing_cash_flows_return_metrics_insufficient_data():
    """6. Missing cash flows -> return metrics INSUFFICIENT_DATA."""
    sources_uses = FundingSourcesUses(total_uses=200000.0, total_sources=200000.0)
    br = banking_ratios_engine.evaluate(cash_flow=None, sources_uses=sources_uses, discount_rate=0.10)
    assert br.return_metrics_status == AppraisalStatus.INSUFFICIENT_DATA
    assert br.reason_code == ReasonCode.MISSING_CASH_FLOWS
    assert br.irr is None
    assert br.npv is None
    assert br.payback_period_years is None


def test_targeted_07_missing_closing_debt_principal_reconciliation_unresolved():
    """7. Missing closing debt -> principal reconciliation UNRESOLVED."""
    loan_mgmt = LoanManagement(
        principal=500000.0,
        annual_interest_rate=10.0,
        monthly_interest_rate=0.0083,
        tenure_months=60,
        monthly_emi=10000.0,
        total_interest=100000.0,
        total_repayment=600000.0
    )
    # 3-year scheduled principal 300k, but closing_debt_final is None (unresolved)
    ds = DebtServiceAnalysisResult(
        status=AppraisalStatus.RESOLVED,
        years=[],
        total_principal=300000.0,
        closing_debt_final=None,
        total_principal_lifetime=None,
        is_zero_debt=False
    )
    val = appraisal_validation_engine.validate(debt_service=ds, loan_management=loan_mgmt)
    p_check = next((c for c in val.checks if c.check_id == "VAL_STAGE9_PRINCIPAL_RECONCILIATION"), None)
    assert p_check is not None
    assert p_check.status == ValidationState.UNRESOLVED
    assert p_check.reason_code == ReasonCode.INSUFFICIENT_DATA
