"""
Financial Viability & DSCR Engine for Stage 9 Financial Engine.
Calculates periodic Debt Service Coverage Ratio (DSCR),
computes an explainable 0–100 Financial Health Score with transparent weights,
determines deterministic Financial Viability classification,
and extracts explicit positive factors and constraints.
"""
from typing import Tuple, List, Dict, Optional
from app.schemas.financial_analysis import (
    DebtServiceAnalysis,
    FinancialViabilityResult,
    FinancialViabilityLevel,
    DSCRStatus,
    CalculationStatus,
    ProjectFinancing,
    CapitalStructure,
    LoanManagement,
    ProfitabilityProjection,
    BreakEvenAnalysis,
    RepaymentSchedule
)
from app.services.financial_engine.constants import (
    DSCR_THRESHOLDS,
    FINANCIAL_HEALTH_WEIGHTS
)


class ViabilityEngine:
    """
    Deterministic financial viability evaluation engine.
    """

    @staticmethod
    def evaluate_debt_service(
        profitability: ProfitabilityProjection,
        loan_management: LoanManagement,
        repayment_schedule: RepaymentSchedule
    ) -> DebtServiceAnalysis:
        """
        Calculates periodic DSCR on consistent quarterly basis.
        """
        if (
            profitability.status != CalculationStatus.CALCULATED or
            profitability.monthly_operating_profit is None or
            profitability.monthly_operating_profit <= 0
        ):
            return DebtServiceAnalysis(
                dscr=None,
                status=DSCRStatus.INSUFFICIENT_DATA,
                operating_cash_flow_basis=None,
                debt_service_basis=None,
                evaluation_notes="DSCR evaluation requires verified operating profit and debt service schedule."
            )

        if loan_management.principal <= 0.0:
            return DebtServiceAnalysis(
                dscr=10.0,
                status=DSCRStatus.STRONG,
                operating_cash_flow_basis=round(profitability.monthly_operating_profit * 3.0, 2),
                debt_service_basis=0.0,
                evaluation_notes="Enterprise operates with 100% equity / zero debt service obligation."
            )

        # Consistent quarterly comparison:
        # Quarterly Operating Cash Flow vs Average Quarterly Debt Service
        quarterly_ocf = round(profitability.monthly_operating_profit * 3.0, 2)
        
        # Determine average quarterly debt service from schedule
        if repayment_schedule.quarterly_schedule:
            # Filter repayment phase quarters (skip zero or interest-only moratorium if evaluating steady-state)
            repay_quarters = [q.total_payment for q in repayment_schedule.quarterly_schedule if q.principal_paid > 0]
            if repay_quarters:
                avg_q_debt = sum(repay_quarters) / len(repay_quarters)
            else:
                avg_q_debt = sum(q.total_payment for q in repayment_schedule.quarterly_schedule) / len(repayment_schedule.quarterly_schedule)
        else:
            avg_q_debt = loan_management.monthly_emi * 3.0

        avg_q_debt = max(1.0, avg_q_debt)
        dscr = round(quarterly_ocf / avg_q_debt, 2)

        if dscr >= DSCR_THRESHOLDS["STRONG"]["min"]:
            status = DSCRStatus.STRONG
            notes = f"DSCR of {dscr}x satisfies institutional lending safety benchmarks (>= 1.5x)."
        elif dscr >= DSCR_THRESHOLDS["ADEQUATE"]["min"]:
            status = DSCRStatus.ADEQUATE
            notes = f"DSCR of {dscr}x provides adequate debt coverage buffer (1.2x - 1.5x)."
        else:
            status = DSCRStatus.WEAK
            notes = f"DSCR of {dscr}x is below recommended minimum threshold of 1.2x; loan service is tight."

        return DebtServiceAnalysis(
            dscr=dscr,
            status=status,
            operating_cash_flow_basis=quarterly_ocf,
            debt_service_basis=round(avg_q_debt, 2),
            evaluation_notes=notes
        )

    @staticmethod
    def evaluate_viability(
        project_financing: ProjectFinancing,
        capital_structure: CapitalStructure,
        loan_management: LoanManagement,
        profitability: ProfitabilityProjection,
        break_even: BreakEvenAnalysis,
        debt_service: DebtServiceAnalysis
    ) -> FinancialViabilityResult:
        """
        Synthesizes composite 0-100 financial health score and viability classification.
        """
        component_scores: Dict[str, float] = {}
        positive_factors: List[str] = []
        constraints: List[str] = []

        # -------------------------------------------------------------------------
        # 1. Component 1: Margin Adequacy (Weight: 0.25)
        # -------------------------------------------------------------------------
        req_margin = max(1.0, project_financing.required_margin)
        avail_margin = project_financing.available_margin

        if avail_margin >= req_margin:
            margin_score = 100.0
            positive_factors.append(
                f"Available margin capital of ₹{avail_margin:,.0f} fully satisfies the required 10% equity contribution (₹{req_margin:,.0f})."
            )
            if project_financing.excess_margin > 0:
                positive_factors.append(
                    f"Surplus margin capital of ₹{project_financing.excess_margin:,.0f} provides additional liquidity cushion."
                )
        else:
            margin_score = max(0.0, round((avail_margin / req_margin) * 100.0, 1))
            deficit = req_margin - avail_margin
            constraints.append(
                f"Available margin capital is ₹{deficit:,.0f} below the required 10% equity contribution for the target project cost."
            )

        component_scores["margin_adequacy"] = margin_score

        # -------------------------------------------------------------------------
        # 2. Component 2: Working Capital Adequacy (Weight: 0.20)
        # -------------------------------------------------------------------------
        wc_allocated = capital_structure.working_capital
        monthly_opex = profitability.monthly_operating_expenses or (capital_structure.total_project_cost * 0.08)
        recommended_wc_buffer = monthly_opex * 2.0

        if wc_allocated >= recommended_wc_buffer:
            wc_score = 100.0
            positive_factors.append(
                f"Working capital allocation of ₹{wc_allocated:,.0f} comfortably exceeds the recommended 2-month operating reserve."
            )
        else:
            wc_score = max(20.0, round((wc_allocated / max(1.0, recommended_wc_buffer)) * 100.0, 1))
            constraints.append(
                f"Working capital allocation of ₹{wc_allocated:,.0f} is tight relative to estimated monthly operational disbursements."
            )

        component_scores["working_capital_adequacy"] = wc_score

        # -------------------------------------------------------------------------
        # 3. Component 3: Debt Service Capacity (Weight: 0.25)
        # -------------------------------------------------------------------------
        if debt_service.dscr is not None:
            dscr_val = debt_service.dscr
            if dscr_val >= 2.0:
                ds_score = 100.0
                positive_factors.append(f"Exceptional Debt Service Coverage Ratio (DSCR: {dscr_val}x) indicates strong repayment robustness.")
            elif dscr_val >= 1.5:
                ds_score = round(85.0 + ((dscr_val - 1.5) / 0.5) * 15.0, 1)
                positive_factors.append(f"Healthy Debt Service Coverage Ratio (DSCR: {dscr_val}x) comfortably satisfies bank underwriting norms.")
            elif dscr_val >= 1.2:
                ds_score = round(70.0 + ((dscr_val - 1.2) / 0.3) * 15.0, 1)
                positive_factors.append(f"Acceptable Debt Service Coverage Ratio (DSCR: {dscr_val}x) covers obligations under standard operation.")
            elif dscr_val >= 1.0:
                ds_score = round(45.0 + ((dscr_val - 1.0) / 0.2) * 25.0, 1)
                constraints.append(f"DSCR of {dscr_val}x leaves minimal cash buffer; sensitive to adverse price or demand shocks.")
            else:
                ds_score = max(0.0, round(dscr_val * 45.0, 1))
                constraints.append(f"Operating cash flow (DSCR: {dscr_val}x) is insufficient to service scheduled monthly EMI.")
        else:
            # Neutral baseline if profitability data is not yet available
            ds_score = 70.0
            if loan_management.principal > 0:
                positive_factors.append(f"Loan repayment structured at ₹{loan_management.monthly_emi:,.0f}/month across {loan_management.tenure_months} months.")

        component_scores["debt_service_capacity"] = ds_score

        # -------------------------------------------------------------------------
        # 4. Component 4: Cash Flow Strength (Weight: 0.15)
        # -------------------------------------------------------------------------
        if profitability.monthly_net_cash_after_debt is not None and profitability.monthly_revenue:
            net_cash = profitability.monthly_net_cash_after_debt
            rev = profitability.monthly_revenue
            cash_margin = (net_cash / rev) * 100.0

            if cash_margin >= 15.0:
                cf_score = 100.0
                positive_factors.append(f"Strong net retained cash flow (₹{net_cash:,.0f}/month, {cash_margin:.1f}% net margin after debt).")
            elif cash_margin >= 8.0:
                cf_score = round(75.0 + ((cash_margin - 8.0) / 7.0) * 25.0, 1)
                positive_factors.append(f"Positive net retained cash flow (₹{net_cash:,.0f}/month after debt service).")
            elif cash_margin > 0.0:
                cf_score = round(50.0 + (cash_margin / 8.0) * 25.0, 1)
                constraints.append(f"Retained net cash surplus (₹{net_cash:,.0f}/month) is modest after debt obligations.")
            else:
                cf_score = max(10.0, round(50.0 + (cash_margin / 10.0) * 40.0, 1))
                constraints.append(f"Negative net cash flow after debt service (Deficit: ₹{abs(net_cash):,.0f}/month).")
        else:
            cf_score = 70.0

        component_scores["cash_flow_strength"] = cf_score

        # -------------------------------------------------------------------------
        # 5. Component 5: Break-Even Strength (Weight: 0.15)
        # -------------------------------------------------------------------------
        if break_even.break_even_utilization_pct is not None:
            util = break_even.break_even_utilization_pct
            if util <= 45.0:
                be_score = 100.0
                positive_factors.append(f"Low break-even threshold ({util:.1f}% capacity) ensures enterprise safety in lean seasons.")
            elif util <= 65.0:
                be_score = round(80.0 + ((65.0 - util) / 20.0) * 20.0, 1)
                positive_factors.append(f"Moderate break-even threshold ({util:.1f}% capacity) provides operational safety.")
            elif util <= 85.0:
                be_score = round(50.0 + ((85.0 - util) / 20.0) * 30.0, 1)
                constraints.append(f"High break-even threshold ({util:.1f}% capacity); business requires sustained high sales volume.")
            else:
                be_score = max(10.0, round(50.0 - ((util - 85.0) / 15.0) * 40.0, 1))
                constraints.append(f"Critical break-even threshold ({util:.1f}% capacity) indicates high sensitivity to fixed overheads.")
        else:
            be_score = 70.0

        component_scores["break_even_strength"] = be_score

        # -------------------------------------------------------------------------
        # 6. Composite Financial Health Score Calculation
        # -------------------------------------------------------------------------
        total_score = sum(
            component_scores[comp] * FINANCIAL_HEALTH_WEIGHTS[comp]
            for comp in FINANCIAL_HEALTH_WEIGHTS
        )
        total_score = round(max(0.0, min(100.0, total_score)), 1)

        # -------------------------------------------------------------------------
        # 7. Viability Classification
        # -------------------------------------------------------------------------
        if profitability.status == CalculationStatus.BENCHMARK_DATA_UNAVAILABLE:
            level = FinancialViabilityLevel.INSUFFICIENT_FINANCIAL_DATA
        elif total_score >= 80.0 and (debt_service.dscr is None or debt_service.dscr >= 1.4):
            level = FinancialViabilityLevel.FINANCIALLY_STRONG
        elif total_score >= 65.0 and (debt_service.dscr is None or debt_service.dscr >= 1.15):
            level = FinancialViabilityLevel.FINANCIALLY_VIABLE
        elif total_score >= 50.0:
            level = FinancialViabilityLevel.FINANCIALLY_CAUTION
        else:
            level = FinancialViabilityLevel.FINANCIALLY_STRESSED

        # Scheme limit constraint note if applicable
        if project_financing.scheme_limited_loan < project_financing.theoretical_loan_requirement:
            diff = project_financing.theoretical_loan_requirement - project_financing.scheme_limited_loan
            constraints.append(
                f"Scheme maximum loan cap (₹{project_financing.scheme_maximum_loan:,.0f}) limited debt by ₹{diff:,.0f}."
            )

        return FinancialViabilityResult(
            level=level,
            financial_health_score=total_score,
            component_scores=component_scores,
            positive_factors=positive_factors,
            constraints=constraints
        )


# Global singleton instance
viability_engine = ViabilityEngine()
