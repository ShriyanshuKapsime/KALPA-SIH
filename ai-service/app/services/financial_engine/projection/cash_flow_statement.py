"""
Cash Flow Statement Engine for Milestone 3.
Models Year 0 capital deployment and Year 1..N operational, investing, and financing cash flows.
Enforces the fundamental identity: Opening Cash + Net Change = Closing Cash.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    CashFlowStatement,
    CashFlowYear,
    ProfitLossStatement,
    WorkingCapitalProjection,
    FundingSourcesUses,
    RepaymentSchedule,
)


class CashFlowStatementEngine:
    """
    Constructs multi-year Cash Flow Statement.
    """

    @staticmethod
    def generate(
        profit_loss: ProfitLossStatement,
        working_capital_proj: WorkingCapitalProjection,
        sources_uses: FundingSourcesUses,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        additional_capex_by_year: Optional[Dict[int, float]] = None,
    ) -> CashFlowStatement:
        """
        Builds Year 0 deployment and Year 1..N Cash Flow Statement.
        """
        add_capex = additional_capex_by_year or {}

        # 1. Year 0 Implementation Deployment (preserve None / explicit 0)
        equity_0 = sources_uses.promoter_contribution
        loan_0 = sources_uses.term_loan
        other_0 = sources_uses.other_financing if sources_uses.other_financing is not None else 0.0
        capex_0 = sources_uses.capex
        inv_0 = sources_uses.opening_inventory
        pre_op_0 = sources_uses.pre_operating_cost
        cont_0 = sources_uses.contingency
        wc_buf_0 = sources_uses.working_capital_buffer

        closing_cash_0: Optional[float] = None
        # All required Year-0 deployment components must be resolved (none may be None)
        # If any required use (capex, inventory, pre-op, contingency) is unknown, closing_cash_0 remains None
        if (
            equity_0 is not None
            and loan_0 is not None
            and capex_0 is not None
            and inv_0 is not None
        ):
            tot_sources = equity_0 + loan_0 + other_0
            tot_capex_deploy = capex_0 + inv_0 + (pre_op_0 or 0.0) + (cont_0 or 0.0)
            # Net cash remaining at Year 0 after initial asset & pre-op deployment
            # Do NOT clamp with max(0.0, ...): funding shortfalls are preserved
            closing_cash_0 = round(tot_sources - tot_capex_deploy, 2)

        year_0_deployment = {
            "equity_inflow": equity_0,
            "loan_inflow": loan_0,
            "capex_outflow": capex_0,
            "opening_inventory_outflow": inv_0,
            "pre_operative_outflow": pre_op_0,
            "contingency_outflow": cont_0,
            "working_capital_buffer": wc_buf_0,
            "closing_cash_balance": closing_cash_0,
        }

        # 2. Extract scheduled principal repayment per year from Stage 9 repayment schedule
        principal_by_year: Dict[int, float] = {}
        has_schedule = bool(repayment_schedule and repayment_schedule.monthly_schedule)
        if has_schedule:
            for row in repayment_schedule.monthly_schedule:
                y = (row.period - 1) // 12 + 1
                val = getattr(row, "principal_component", getattr(row, "principal_paid", 0.0))
                principal_by_year[y] = round(principal_by_year.get(y, 0.0) + float(val), 2)

        years: List[CashFlowYear] = []
        current_cash = closing_cash_0
        term_loan_val = sources_uses.term_loan

        wc_map = {y.year: y for y in working_capital_proj.years}

        for pl_line in profit_loss.years:
            y = pl_line.year
            pat = pl_line.profit_after_tax
            pbt = getattr(pl_line, "profit_before_tax", getattr(pl_line, "pbt", None))
            depr = pl_line.depreciation if pl_line.depreciation is not None else None

            wc_line = wc_map.get(y)
            # Change in working capital: None means unknown, not zero
            delta_wc = wc_line.change_in_working_capital if wc_line else None

            # Cash from operations — strictly uses final resolved PAT where tax is applicable.
            # Do not generate a final CFO substituting PBT while tax is still unresolved.
            is_exempt = getattr(pl_line, "tax_status", None) == "EXEMPT"
            if is_exempt:
                op_profit_basis = pbt
            elif pat is not None:
                op_profit_basis = pat
            else:
                op_profit_basis = None

            cfo: Optional[float] = None
            if op_profit_basis is not None and depr is not None:
                if delta_wc is not None:
                    cfo = round(op_profit_basis + depr - delta_wc, 2)
                else:
                    cfo = None

            # Cash from investing (additional CapEx)
            capex_y = round(add_capex.get(y, 0.0), 2)
            cfi = round(-capex_y, 2)

            # Cash from financing (Principal repayment)
            # IF term loan == 0: principal repayment = 0.0
            # ELIF Stage 9 repayment schedule exists: use scheduled principal
            # ELSE: principal repayment = None
            prin_repaid: Optional[float] = None
            if term_loan_val == 0.0:
                prin_repaid = 0.0
            elif has_schedule:
                prin_repaid = principal_by_year.get(y, 0.0)
            else:
                prin_repaid = None

            cff: Optional[float] = round(-prin_repaid, 2) if prin_repaid is not None else None

            # Net change in cash
            net_change: Optional[float] = None
            closing_cash: Optional[float] = None
            opening_cash = round(current_cash, 2) if current_cash is not None else None

            if cfo is not None and opening_cash is not None and cff is not None:
                net_change = round(cfo + cfi + cff, 2)
                closing_cash = round(opening_cash + net_change, 2)
                current_cash = closing_cash
            else:
                # Cannot determine closing cash — propagate unknown
                current_cash = None

            cf_status = "RESOLVED"
            if cfo is None or closing_cash is None or prin_repaid is None:
                cf_status = "PARTIALLY_DERIVED"

            years.append(
                CashFlowYear(
                    year=y,
                    profit_after_tax=pat,
                    depreciation=depr,
                    change_in_working_capital=delta_wc,
                    cash_from_operations=cfo,
                    capex_outflow=capex_y,
                    cash_from_investing=cfi,
                    equity_inflow=0.0,
                    loan_disbursement=0.0,
                    principal_repayment=prin_repaid,
                    cash_from_financing=cff,
                    net_change_in_cash=net_change,
                    opening_cash_balance=opening_cash,
                    closing_cash_balance=closing_cash,
                    status=cf_status
                )
            )

        overall_status = "RESOLVED" if all(y.status == "RESOLVED" for y in years) else "PARTIALLY_DERIVED"
        cash_str = f"₹{closing_cash_0:,.2f}" if closing_cash_0 is not None else "unresolved"

        return CashFlowStatement(
            status=overall_status,
            year_0_deployment=year_0_deployment,
            years=years,
            notes=f"Cash flow projected over {len(years)} years with Year 0 opening cash {cash_str}."
        )


cash_flow_statement_engine = CashFlowStatementEngine()
