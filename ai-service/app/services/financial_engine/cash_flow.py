"""
Cash Flow Engine for Stage 9 Financial Engine.
Models Month 0 capital deployment, 12-month detailed cash-flow projection,
and 3-year annual liquidity summary.
"""
from typing import List, Optional
from app.schemas.financial_analysis import (
    Month0Deployment,
    MonthlyCashFlowRow,
    AnnualCashFlowSummary,
    CashFlowAnalysis,
    CalculationStatus,
    ProjectFinancing,
    CapitalStructure,
    LoanManagement,
    ProfitabilityProjection,
    RepaymentSchedule
)


class CashFlowEngine:
    """
    Deterministic cash flow modeling engine.
    """

    @staticmethod
    def project_cash_flows(
        project_financing: ProjectFinancing,
        capital_structure: CapitalStructure,
        loan_management: LoanManagement,
        profitability: ProfitabilityProjection,
        repayment_schedule: RepaymentSchedule
    ) -> CashFlowAnalysis:
        """
        Builds Month 0 deployment, 12-month operational cash flow, and 3-year annual summary.
        """
        # 1. Month 0 Deployment
        margin_inj = capital_structure.margin_contribution
        loan_in = capital_structure.loan_component
        capex_out = capital_structure.fixed_capital_capex
        wc_alloc = capital_structure.working_capital
        closing_cash_m0 = wc_alloc

        month_0 = Month0Deployment(
            margin_injection=margin_inj,
            loan_inflow=loan_in,
            capex_outflow=capex_out,
            working_capital_allocation=wc_alloc,
            closing_cash_balance=closing_cash_m0
        )

        # 2. Check if profitability was calculable
        if profitability.status != CalculationStatus.CALCULATED or profitability.monthly_revenue is None:
            return CashFlowAnalysis(
                status=CalculationStatus.BENCHMARK_DATA_UNAVAILABLE,
                month_0_deployment=month_0,
                monthly_projection=[],
                annual_summary=[],
                notes="Operational cash flow projection requires verified profitability benchmarks or user inputs."
            )

        monthly_rev = profitability.monthly_revenue
        monthly_cogs = profitability.monthly_cogs or 0.0
        monthly_opex = profitability.monthly_operating_expenses or 0.0

        monthly_rows: List[MonthlyCashFlowRow] = []
        current_cash = closing_cash_m0

        # Build map of month -> debt service payment from repayment schedule
        debt_payment_by_month = {}
        for row in repayment_schedule.monthly_schedule:
            debt_payment_by_month[row.period] = row.payment

        # 3. 12-Month Projection
        for m in range(1, 13):
            opening_c = round(current_cash, 2)
            rev_in = monthly_rev
            cogs_out = monthly_cogs
            opex_out = monthly_opex
            debt_out = debt_payment_by_month.get(m, loan_management.monthly_emi)

            total_out = round(cogs_out + opex_out + debt_out, 2)
            net_flow = round(rev_in - total_out, 2)
            closing_c = round(opening_c + net_flow, 2)

            monthly_rows.append(
                MonthlyCashFlowRow(
                    month=m,
                    opening_cash=opening_c,
                    revenue_inflow=rev_in,
                    cogs_outflow=cogs_out,
                    opex_outflow=opex_out,
                    debt_service_outflow=debt_out,
                    total_outflows=total_out,
                    net_cash_flow=net_flow,
                    closing_cash=closing_c
                )
            )
            current_cash = closing_c

        # 4. 3-Year Annual Summary
        annual_rows: List[AnnualCashFlowSummary] = []
        
        # Year 1 (Sum of months 1-12)
        y1_rev = sum(r.revenue_inflow for r in monthly_rows)
        y1_exp = sum(r.cogs_outflow + r.opex_outflow for r in monthly_rows)
        y1_debt = sum(r.debt_service_outflow for r in monthly_rows)
        y1_net = y1_rev - (y1_exp + y1_debt)
        y1_closing = monthly_rows[-1].closing_cash

        annual_rows.append(
            AnnualCashFlowSummary(
                year=1,
                annual_revenue=round(y1_rev, 2),
                annual_expenses=round(y1_exp, 2),
                annual_debt_service=round(y1_debt, 2),
                annual_net_cash_flow=round(y1_net, 2),
                closing_cash_balance=round(y1_closing, 2)
            )
        )

        # Year 2 (Modest 5% operational maturity growth)
        y2_rev = y1_rev * 1.05
        y2_exp = y1_exp * 1.04
        y2_debt = sum(debt_payment_by_month.get(m, loan_management.monthly_emi) for m in range(13, 25))
        y2_net = y2_rev - (y2_exp + y2_debt)
        y2_closing = y1_closing + y2_net

        annual_rows.append(
            AnnualCashFlowSummary(
                year=2,
                annual_revenue=round(y2_rev, 2),
                annual_expenses=round(y2_exp, 2),
                annual_debt_service=round(y2_debt, 2),
                annual_net_cash_flow=round(y2_net, 2),
                closing_cash_balance=round(y2_closing, 2)
            )
        )

        # Year 3 (Further 5% growth)
        y3_rev = y2_rev * 1.05
        y3_exp = y2_exp * 1.04
        y3_debt = sum(debt_payment_by_month.get(m, loan_management.monthly_emi) for m in range(25, 37))
        y3_net = y3_rev - (y3_exp + y3_debt)
        y3_closing = y2_closing + y3_net

        annual_rows.append(
            AnnualCashFlowSummary(
                year=3,
                annual_revenue=round(y3_rev, 2),
                annual_expenses=round(y3_exp, 2),
                annual_debt_service=round(y3_debt, 2),
                annual_net_cash_flow=round(y3_net, 2),
                closing_cash_balance=round(y3_closing, 2)
            )
        )

        return CashFlowAnalysis(
            status=CalculationStatus.CALCULATED,
            month_0_deployment=month_0,
            monthly_projection=monthly_rows,
            annual_summary=annual_rows,
            notes="Deterministic 12-month and 3-year cash flow forecast based on verified cost and repayment schedule."
        )


# Global singleton instance
cash_flow_engine = CashFlowEngine()
