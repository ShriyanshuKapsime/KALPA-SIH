"""
Projected Balance Sheet Engine for Milestone 3.
Implements multi-year Balance Sheet (Assets = Liabilities + Equity) with mandatory reconciliation.
Zero balancing plugs. Reconciles directly with P&L, Cash Flow, and Loan Amortization.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    BalanceSheet,
    BalanceSheetYear,
    ProfitLossStatement,
    CashFlowStatement,
    WorkingCapitalProjection,
    FundingSourcesUses,
    RepaymentSchedule,
)
from app.services.financial_engine.projection.depreciation import DepreciationScheduleYear


class BalanceSheetEngine:
    """
    Constructs multi-year Balance Sheet with strict double-entry reconciliation.
    """

    @staticmethod
    def generate(
        profit_loss: ProfitLossStatement,
        cash_flow: CashFlowStatement,
        working_capital_proj: WorkingCapitalProjection,
        sources_uses: FundingSourcesUses,
        depreciation_schedule: Dict[int, DepreciationScheduleYear],
        repayment_schedule: Optional[RepaymentSchedule] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
    ) -> BalanceSheet:
        """
        Generates Year 1..N Balance Sheet and validates accounting equality.
        """
        user_in = user_inputs or {}
        asm_map = assumptions_map or {}

        # 1. Promoter Equity Baseline (preserve None/explicit 0)
        promoter_equity: Optional[float] = sources_uses.promoter_contribution

        # Pre-operative asset & amortization (no hardcoded 5-year assumption)
        pre_op_total: Optional[float] = sources_uses.pre_operating_cost
        pre_op_annual_amort: Optional[float] = None

        if pre_op_total is not None:
            if pre_op_total == 0.0:
                pre_op_annual_amort = 0.0
            else:
                amort_years = user_in.get("pre_op_amortization_years") or user_in.get("pre_operative_amortization_years")
                if amort_years is None and asm_map:
                    raw_ay = asm_map.get("pre_op_amortization_years")
                    amort_years = getattr(raw_ay, "value", raw_ay)
                else:
                    amort_years = getattr(amort_years, "value", amort_years)
                if amort_years is not None:
                    try:
                        ay = float(amort_years)
                        if ay > 0:
                            pre_op_annual_amort = round(pre_op_total / ay, 2)
                    except (ValueError, TypeError):
                        pass
                # If no valid amortization period is evidenced, remains None (unresolved)

        # 2. Extract scheduled closing loan balance per year from Stage 9 repayment schedule
        closing_debt_by_year: Dict[int, Optional[float]] = {}
        initial_loan = sources_uses.term_loan

        if repayment_schedule and repayment_schedule.monthly_schedule:
            # Map year -> closing balance at month y*12
            total_months = len(repayment_schedule.monthly_schedule)
            for y in range(1, 11):
                target_month = y * 12
                if target_month <= total_months:
                    row = repayment_schedule.monthly_schedule[target_month - 1]
                    closing_debt_by_year[y] = round(float(row.closing_balance), 2)
                elif total_months > 0:
                    closing_debt_by_year[y] = 0.0
        elif initial_loan == 0.0:
            # Structurally zero debt
            for y in range(1, len(profit_loss.years) + 1):
                closing_debt_by_year[y] = 0.0
        elif initial_loan is not None and initial_loan > 0.0:
            cur_debt: Optional[float] = initial_loan
            cf_map_p = {c.year: c.principal_repayment for c in cash_flow.years}
            for y in range(1, len(profit_loss.years) + 1):
                repaid = cf_map_p.get(y)
                if repaid is not None and cur_debt is not None:
                    cur_debt = round(max(0.0, cur_debt - repaid), 2)
                    closing_debt_by_year[y] = cur_debt
                else:
                    cur_debt = None
                    closing_debt_by_year[y] = None
        else:
            # Loan is unknown
            for y in range(1, len(profit_loss.years) + 1):
                closing_debt_by_year[y] = None

        years: List[BalanceSheetYear] = []
        cumulative_pat: Optional[float] = 0.0
        all_balanced: bool = True
        diagnostics_list: List[str] = []

        cf_map = {c.year: c for c in cash_flow.years}
        wc_map = {w.year: w for w in working_capital_proj.years}

        for pl_line in profit_loss.years:
            y = pl_line.year
            pat = pl_line.profit_after_tax
            is_exempt = getattr(pl_line, "tax_status", None) == "EXEMPT"
            earnings = pat if pat is not None else (pbt if is_exempt else None)
            if earnings is not None and cumulative_pat is not None:
                cumulative_pat = round(cumulative_pat + earnings, 2)
            else:
                cumulative_pat = None

            # --- ASSETS ---
            # Net Fixed Assets (Net PPE)
            depr_info = depreciation_schedule.get(y)
            depr_resolved = (
                depr_info is not None
                and getattr(depr_info, "status", "RESOLVED") == "RESOLVED"
                and depr_info.accumulated_depreciation is not None
                and depr_info.net_block is not None
            )

            gross_ppe: Optional[float] = None
            accum_depr: Optional[float] = None
            net_ppe: Optional[float] = None

            if sources_uses.capex == 0.0:
                # Structural zero CapEx
                gross_ppe = 0.0
                accum_depr = 0.0
                net_ppe = 0.0
            elif depr_resolved and depr_info.gross_block is not None:
                gross_ppe = depr_info.gross_block
                accum_depr = depr_info.accumulated_depreciation
                net_ppe = depr_info.net_block
            elif sources_uses.capex is not None or (depr_info is not None and depr_info.gross_block is not None):
                gross_ppe = sources_uses.capex if sources_uses.capex is not None else depr_info.gross_block
                accum_depr = None
                net_ppe = None

            # Current Assets
            wc_line = wc_map.get(y)
            inv = wc_line.inventory if wc_line else None
            rec = wc_line.receivables if wc_line else None

            cf_line = cf_map.get(y)
            cash = cf_line.closing_cash_balance if cf_line else None

            # Remaining unamortized pre-operative asset (if any)
            unamortized_pre_op: Optional[float] = None
            if pre_op_total == 0.0:
                unamortized_pre_op = 0.0
            elif pre_op_total is not None and pre_op_annual_amort is not None:
                unamortized_pre_op = round(max(0.0, pre_op_total - (pre_op_annual_amort * y)), 2)

            # Compute totals only if ALL components are known
            total_ca: Optional[float] = None
            total_assets: Optional[float] = None

            if inv is not None and rec is not None and cash is not None:
                total_ca = round(inv + rec + cash, 2)
                # If pre_op exists but amortization is unresolved, assets cannot be fully resolved
                if net_ppe is not None and (pre_op_total is None or unamortized_pre_op is not None):
                    pre_op_val = unamortized_pre_op if unamortized_pre_op is not None else 0.0
                    total_assets = round(net_ppe + pre_op_val + total_ca, 2)

            # --- LIABILITIES ---
            term_debt = closing_debt_by_year.get(y)
            payables = wc_line.payables if (wc_line and wc_line.payables is not None) else None

            total_liab: Optional[float] = None
            if term_debt is not None and payables is not None:
                total_liab = round(term_debt + payables, 2)

            # --- EQUITY ---
            total_equity: Optional[float] = None
            if promoter_equity is not None and cumulative_pat is not None:
                total_equity = round(promoter_equity + cumulative_pat, 2)

            total_liab_equity: Optional[float] = None
            if total_liab is not None and total_equity is not None:
                total_liab_equity = round(total_liab + total_equity, 2)

            # Double-Entry Verification
            diff: Optional[float] = None
            is_balanced = False
            year_status = "PARTIALLY_DERIVED"

            if total_assets is not None and total_liab_equity is not None:
                diff = round(total_assets - total_liab_equity, 2)
                is_balanced = abs(diff) <= 1.0
                year_status = "RESOLVED" if is_balanced else "FAILED"
            elif total_assets is None and total_liab_equity is None:
                year_status = "UNKNOWN"
            else:
                year_status = "PARTIALLY_DERIVED"

            if not is_balanced:
                all_balanced = False
                if diff is not None:
                    diag = f"Year {y} Unbalanced: Assets {total_assets:,.2f} != Liab+Equity {total_liab_equity:,.2f} (diff: {diff:,.2f})"
                    diagnostics_list.append(diag)
                else:
                    diagnostics_list.append(f"Year {y}: Insufficient data for balance sheet reconciliation.")

            years.append(
                BalanceSheetYear(
                    year=y,
                    gross_fixed_assets=gross_ppe,
                    accumulated_depreciation=accum_depr,
                    net_fixed_assets=net_ppe,
                    inventory=inv,
                    trade_receivables=rec,
                    cash_and_bank=cash,
                    other_current_assets=unamortized_pre_op if (unamortized_pre_op is not None and unamortized_pre_op > 0) else None,
                    total_current_assets=total_ca,
                    total_assets=total_assets,
                    term_loan_outstanding=term_debt,
                    trade_payables=payables,
                    other_current_liabilities=0.0 if payables is not None else None,
                    total_liabilities=total_liab,
                    promoter_capital=promoter_equity,
                    retained_earnings=cumulative_pat,
                    total_equity=total_equity,
                    total_liabilities_and_equity=total_liab_equity,
                    reconciliation_difference=diff,
                    is_balanced=is_balanced,
                    status=year_status
                )
            )

        # Distinguish: BALANCED, FAILED, PARTIALLY_DERIVED / INSUFFICIENT_DATA
        if not years:
            overall_status = "INSUFFICIENT_DATA"
        elif any(y.status == "FAILED" for y in years):
            overall_status = "FAILED"
        elif any(y.status in ("PARTIALLY_DERIVED", "UNKNOWN", "INSUFFICIENT_DATA") for y in years):
            overall_status = "PARTIALLY_DERIVED"
        elif all(y.is_balanced for y in years):
            overall_status = "BALANCED"
        else:
            overall_status = "FAILED"

        diag_msg = "; ".join(diagnostics_list) if diagnostics_list else "All balance sheet projection years strictly reconciled."

        return BalanceSheet(
            status=overall_status,
            years=years,
            reconciliation_diagnostics=diag_msg
        )


balance_sheet_engine = BalanceSheetEngine()
