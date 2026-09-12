"""
Comprehensive Deterministic Test Suite for Stage 9: Financial Engine.
Covers 18 test scenarios validating scheme routing, loan caps, EMI annuity formulas,
moratorium interest, zero-penny amortization closure, DSCR, break-even,
missing benchmark handling, user overrides, and zero hardcoded demo data regression.
"""
import pytest
from app.services.financial_engine import (
    financial_engine,
    loan_calculator,
    amortization_engine,
    capital_allocation_engine,
    profitability_engine,
    break_even_engine,
    viability_engine,
    financial_benchmark_adapter,
    SCHEME_RULES,
    MORATORIUM_MODES,
    DSCR_THRESHOLDS,
    FINANCIAL_HEALTH_WEIGHTS
)
from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialCalculatorRequest,
    FinancialProfileInput,
    BusinessProfileInput,
    LocationProfileInput,
    ProjectAssumptionsInput,
    SchemeType,
    CalculationStatus,
    DSCRStatus,
    FinancialViabilityLevel,
    MoratoriumInterestMode
)


class TestStage9FinancialEngine:
    """
    Automated test verification suite for Stage 9 Deterministic Financial Engine.
    """

    # -------------------------------------------------------------------------
    # Test 1: ₹10,000 Margin -> Micro Finance Scheme
    # -------------------------------------------------------------------------
    def test_01_micro_finance_scheme_routing_10k_margin(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=10000.0)
        
        assert proj_fin.available_margin == 10000.0
        assert proj_fin.theoretical_project_cost == 100000.0
        assert proj_fin.theoretical_loan_requirement == 90000.0
        assert scheme_res.recommended_scheme == SchemeType.MICRO_FINANCE_SCHEME
        assert scheme_res.status == "MATCHED"
        assert proj_fin.estimated_financeable_loan == 90000.0
        assert proj_fin.excess_margin == 0.0

    # -------------------------------------------------------------------------
    # Test 2: ₹14,000 Margin Boundary (₹1,40,000 Project Cost -> Micro Finance)
    # -------------------------------------------------------------------------
    def test_02_margin_boundary_14k_micro_finance(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=14000.0)
        
        assert proj_fin.theoretical_project_cost == 140000.0
        assert proj_fin.theoretical_loan_requirement == 126000.0
        assert scheme_res.recommended_scheme == SchemeType.MICRO_FINANCE_SCHEME
        # Loan cap on Micro Finance is ₹1,25,000
        assert proj_fin.scheme_maximum_loan == 125000.0
        assert proj_fin.scheme_limited_loan == 125000.0
        assert proj_fin.estimated_financeable_loan == 125000.0
        assert proj_fin.excess_margin > 0.0

    # -------------------------------------------------------------------------
    # Test 3: ₹14,001 Margin Boundary (₹1,40,010 Project Cost -> Term Loan)
    # -------------------------------------------------------------------------
    def test_03_margin_boundary_14001_term_loan(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=14001.0)
        
        assert proj_fin.theoretical_project_cost == 140010.0
        assert scheme_res.recommended_scheme == SchemeType.TERM_LOAN_SCHEME
        assert scheme_res.status == "MATCHED"
        assert proj_fin.scheme_maximum_loan == 4500000.0
        assert proj_fin.estimated_financeable_loan == round(140010.0 * 0.90, 2)

    # -------------------------------------------------------------------------
    # Test 4: ₹1,00,000 Margin -> Term Loan (₹10,00,000 Project Cost)
    # -------------------------------------------------------------------------
    def test_04_term_loan_100k_margin(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=100000.0)
        
        assert proj_fin.available_margin == 100000.0
        assert proj_fin.theoretical_project_cost == 1000000.0
        assert proj_fin.theoretical_loan_requirement == 900000.0
        assert scheme_res.recommended_scheme == SchemeType.TERM_LOAN_SCHEME
        assert proj_fin.estimated_financeable_loan == 900000.0
        assert proj_fin.excess_margin == 0.0

    # -------------------------------------------------------------------------
    # Test 5: Maximum Supported Term Loan Boundary (₹50 Lakh Project Cost)
    # -------------------------------------------------------------------------
    def test_05_max_supported_term_loan_boundary_50lakh(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=500000.0)
        
        assert proj_fin.theoretical_project_cost == 5000000.0
        assert proj_fin.theoretical_loan_requirement == 4500000.0
        assert scheme_res.recommended_scheme == SchemeType.TERM_LOAN_SCHEME
        assert proj_fin.estimated_financeable_loan == 4500000.0

    # -------------------------------------------------------------------------
    # Test 6: Above ₹50 Lakh Project Cost -> NO_SUPPORTED_SCHEME
    # -------------------------------------------------------------------------
    def test_06_above_50_lakh_no_supported_scheme(self):
        scheme_res, proj_fin, cfg = loan_calculator.calculate_project_financing(available_margin_capital=600000.0)
        
        assert proj_fin.theoretical_project_cost == 6000000.0
        assert scheme_res.recommended_scheme == SchemeType.NO_SUPPORTED_SCHEME
        assert scheme_res.status == "NO_SUPPORTED_SCHEME"
        assert "Calculated project cost exceeds the configured maximum scheme limit" in scheme_res.eligibility_notes[0]
        assert proj_fin.estimated_financeable_loan == 0.0

    # -------------------------------------------------------------------------
    # Test 7: Loan Cap Enforcement (Micro cap ₹1.25L, Term Loan cap ₹45L)
    # -------------------------------------------------------------------------
    def test_07_loan_cap_enforcement(self):
        # Micro Scheme Cap
        scheme_res_micro, proj_fin_micro, _ = loan_calculator.calculate_project_financing(
            available_margin_capital=13900.0 # Cost: 1,39,000, 90% Loan: 1,25,100 -> Capped at 1,25,000
        )
        assert proj_fin_micro.theoretical_loan_requirement == 125100.0
        assert proj_fin_micro.estimated_financeable_loan == 125000.0

        # Term Loan Cap
        scheme_res_term, proj_fin_term, _ = loan_calculator.calculate_project_financing(
            available_margin_capital=550000.0 # Cost: 5,500,000 -> Exceeds limit
        )
        assert scheme_res_term.recommended_scheme == SchemeType.NO_SUPPORTED_SCHEME

    # -------------------------------------------------------------------------
    # Test 8: Micro Finance EMI Formula & Interest Accuracy
    # -------------------------------------------------------------------------
    def test_08_micro_finance_emi_calculation(self):
        # Principal: 90,000, Rate: 6.5%, Tenure: 36 months, Moratorium: 3 months -> Repayment: 33 months
        loan_mgmt = loan_calculator.calculate_emi(
            principal=90000.0,
            annual_rate=0.065,
            tenure_months=36,
            moratorium_months=3,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )
        
        assert loan_mgmt.principal == 90000.0
        assert loan_mgmt.annual_interest_rate == 0.065
        assert loan_mgmt.tenure_months == 36
        assert loan_mgmt.moratorium_months == 3
        
        # Monthly interest rate = 0.065 / 12 = 0.005416666...
        # Moratorium interest = 3 * (90000 * 0.065 / 12) = 1462.50
        assert abs(loan_mgmt.moratorium_interest_total - 1462.50) < 1.0
        
        # EMI for 90k over 33 months at 6.5% p.a.
        # r = 0.065 / 12 = 0.00541667; n = 33
        # (1+r)^33 = 1.19504; EMI ≈ 90000 * 0.00541667 * 1.19504 / 0.19504 ≈ 2988.42
        assert 2950.0 < loan_mgmt.monthly_emi < 3050.0
        assert loan_mgmt.total_repayment > loan_mgmt.principal

    # -------------------------------------------------------------------------
    # Test 9: Term Loan EMI Formula & Interest Accuracy
    # -------------------------------------------------------------------------
    def test_09_term_loan_emi_calculation(self):
        # Principal: 900,000, Rate: 8.0%, Tenure: 84 months, Moratorium: 6 months -> Repayment: 78 months
        loan_mgmt = loan_calculator.calculate_emi(
            principal=900000.0,
            annual_rate=0.080,
            tenure_months=84,
            moratorium_months=6,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )
        
        assert loan_mgmt.principal == 900000.0
        assert loan_mgmt.annual_interest_rate == 0.08
        assert loan_mgmt.tenure_months == 84
        assert loan_mgmt.moratorium_months == 6
        
        # Monthly interest rate = 0.08 / 12 = 0.00666667
        # Moratorium interest = 6 * (900000 * 0.08 / 12) = 36000.0
        assert abs(loan_mgmt.moratorium_interest_total - 36000.0) < 1.0
        
        # EMI for 900k over 78 months at 8.0% p.a.
        # Approx ₹14,845 / month
        assert 14500.0 < loan_mgmt.monthly_emi < 15200.0
        assert loan_mgmt.total_interest > 250000.0

    # -------------------------------------------------------------------------
    # Test 10: Moratorium Calculation Assumption
    # -------------------------------------------------------------------------
    def test_10_moratorium_assumption_statement(self):
        loan_mgmt = loan_calculator.calculate_emi(
            principal=500000.0,
            annual_rate=0.08,
            tenure_months=60,
            moratorium_months=6,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )
        assert "Moratorium calculation assumption" in loan_mgmt.assumption_statement
        assert "Interest serviced monthly" in loan_mgmt.assumption_statement

    # -------------------------------------------------------------------------
    # Test 11: Amortization Schedule Ending Balance ≈ 0.0
    # -------------------------------------------------------------------------
    def test_11_amortization_schedule_zero_closing_balance(self):
        schedule = amortization_engine.generate_schedule(
            principal=900000.0,
            annual_rate=0.08,
            tenure_months=84,
            moratorium_months=6,
            monthly_emi=14845.0,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )
        
        assert len(schedule.monthly_schedule) == 84
        assert schedule.first_repayment_month == 7
        
        # Check Moratorium rows (months 1-6)
        for row in schedule.monthly_schedule[:6]:
            assert row.phase == "MORATORIUM"
            assert row.principal_component == 0.0
            assert row.closing_balance == 900000.0
            assert row.payment == row.interest_component

        # Check final row (month 84) strictly equals 0.0
        final_row = schedule.monthly_schedule[-1]
        assert final_row.phase == "REPAYMENT"
        assert final_row.closing_balance == 0.0

    # -------------------------------------------------------------------------
    # Test 12: Quarterly Repayment Schedule Correctness
    # -------------------------------------------------------------------------
    def test_12_quarterly_schedule_correctness(self):
        schedule = amortization_engine.generate_schedule(
            principal=360000.0,
            annual_rate=0.08,
            tenure_months=36,
            moratorium_months=3,
            monthly_emi=12200.0,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )
        
        # 36 months / 3 = 12 quarters
        assert len(schedule.quarterly_schedule) == 12
        q1 = schedule.quarterly_schedule[0]
        assert q1.quarter == 1
        assert q1.months == [1, 2, 3]
        assert q1.principal_paid == 0.0  # Q1 is moratorium
        
        final_q = schedule.quarterly_schedule[-1]
        assert final_q.closing_balance == 0.0

    # -------------------------------------------------------------------------
    # Test 13: Break-Even Calculation
    # -------------------------------------------------------------------------
    def test_13_break_even_calculation(self):
        # Mock profitability
        from app.schemas.financial_analysis import ProfitabilityProjection
        prof = ProfitabilityProjection(
            status=CalculationStatus.CALCULATED,
            monthly_revenue=100000.0,
            annual_revenue=1200000.0,
            monthly_cogs=60000.0,
            monthly_gross_profit=40000.0,
            monthly_operating_expenses=20000.0,
            monthly_operating_profit=20000.0
        )
        assumptions = ProjectAssumptionsInput(expected_monthly_units=1000, expected_unit_price=100)
        
        be = break_even_engine.calculate_break_even(prof, assumptions, None)
        assert be.status == CalculationStatus.CALCULATED
        assert be.contribution_margin is not None
        assert be.monthly_break_even_revenue is not None
        assert be.break_even_utilization_pct is not None
        assert 0.0 < be.break_even_utilization_pct < 100.0

    # -------------------------------------------------------------------------
    # Test 14: DSCR Calculation & Status Classification
    # -------------------------------------------------------------------------
    def test_14_dscr_calculation_and_status(self):
        from app.schemas.financial_analysis import ProfitabilityProjection, LoanManagement
        prof_strong = ProfitabilityProjection(
            status=CalculationStatus.CALCULATED,
            monthly_operating_profit=30000.0
        )
        loan_mgmt = LoanManagement(
            principal=500000.0,
            annual_interest_rate=0.08,
            monthly_interest_rate=0.08/12,
            tenure_months=84,
            moratorium_months=6,
            monthly_emi=10000.0,
            total_interest=100000.0,
            total_repayment=600000.0
        )
        schedule = amortization_engine.generate_schedule(500000.0, 0.08, 84, 6, 10000.0)
        
        # Quarterly OCF = 30k * 3 = 90k; Quarterly Debt ≈ 29k-30k -> DSCR ≈ 3.0-3.1 (Strong)
        res = viability_engine.evaluate_debt_service(prof_strong, loan_mgmt, schedule)
        assert res.status == DSCRStatus.STRONG
        assert 2.8 <= res.dscr <= 3.2

    # -------------------------------------------------------------------------
    # Test 15: Missing Benchmark Data (BENCHMARK_DATA_UNAVAILABLE)
    # -------------------------------------------------------------------------
    def test_15_missing_benchmark_data_handling(self):
        req = FinancialAnalysisRequest(
            analysis_id="test_missing_bench",
            financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
            business_profile=BusinessProfileInput(business_id="non_existent_exotic_business_xyz_123"),
            project_assumptions=ProjectAssumptionsInput()
        )
        
        resp = financial_engine.analyze(req)
        assert resp.financial_analysis.scheme_result.status == "MATCHED"
        assert resp.financial_analysis.loan_management.monthly_emi > 0
        # Profitability must be labeled BENCHMARK_DATA_UNAVAILABLE rather than inventing numbers
        assert resp.financial_analysis.profitability.status == CalculationStatus.BENCHMARK_DATA_UNAVAILABLE
        assert resp.financial_analysis.financial_viability.level == FinancialViabilityLevel.INSUFFICIENT_FINANCIAL_DATA

    # -------------------------------------------------------------------------
    # Test 16: User Override of Benchmark Assumptions
    # -------------------------------------------------------------------------
    def test_16_user_override_benchmark_data(self):
        req = FinancialAnalysisRequest(
            analysis_id="test_user_override",
            financial_profile=FinancialProfileInput(available_margin_capital=100000.0),
            business_profile=BusinessProfileInput(business_id="rice_mill"),
            project_assumptions=ProjectAssumptionsInput(
                expected_monthly_revenue=250000.0,
                capex_override=600000.0,
                working_capital_override=400000.0
            )
        )
        
        resp = financial_engine.analyze(req)
        fin = resp.financial_analysis
        assert fin.profitability.monthly_revenue == 250000.0
        assert fin.profitability.source == "USER_INPUT"
        assert fin.capital_structure.capex_percentage == 60.0
        assert fin.capital_structure.working_capital_percentage == 40.0
        assert fin.capital_structure.source == "USER_INPUT"

    # -------------------------------------------------------------------------
    # Test 17: Real Active Analysis Context Integration
    # -------------------------------------------------------------------------
    def test_17_real_active_analysis_context(self):
        req = FinancialAnalysisRequest(
            analysis_id="real_active_session_456",
            session_id="session_789",
            financial_profile=FinancialProfileInput(available_margin_capital=75000.0),
            business_profile=BusinessProfileInput(
                business_id="flour_mill",
                specific_business="Commercial Atta Chakki Unit",
                category="Grain Milling",
                nic_code="10611"
            ),
            location_profile=LocationProfileInput(
                district="Surat",
                state="Gujarat"
            )
        )
        
        resp = financial_engine.analyze(req)
        assert resp.analysis_id == "real_active_session_456"
        assert resp.session_id == "session_789"
        assert resp.financial_analysis.project_financing.available_margin == 75000.0
        assert resp.financial_analysis.project_financing.theoretical_project_cost == 750000.0
        assert resp.financial_analysis.scheme_result.recommended_scheme == SchemeType.TERM_LOAN_SCHEME

    # -------------------------------------------------------------------------
    # Test 18: Standalone Calculator Endpoint Execution
    # -------------------------------------------------------------------------
    def test_18_standalone_calculator_endpoint(self):
        req = FinancialCalculatorRequest(
            available_margin_capital=120000.0
        )
        calc_resp = financial_engine.calculate(req)
        assert calc_resp.status == "SUCCESS"
        res = calc_resp.calculator_result
        assert res.available_margin_capital == 120000.0
        assert res.theoretical_project_cost == 1200000.0
        assert res.estimated_loan_requirement == 1080000.0
        assert res.monthly_emi > 0
        assert res.estimated_quarterly_obligation > 0
        assert "ESTIMATE / CALCULATION" in res.label
