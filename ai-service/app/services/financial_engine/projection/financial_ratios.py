"""
Financial Ratios Engine for Milestone 3.
Calculates institutional profitability, liquidity, leverage, debt service, and efficiency ratios.
Enforces strict zero-division protection throughout.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    FinancialRatioSet,
    FinancialRatioYear,
    ProfitLossStatement,
    BalanceSheet,
    WorkingCapitalProjection,
    CashFlowStatement,
)


class FinancialRatiosEngine:
    """
    Computes multi-year institutional financial ratios.
    """

    @staticmethod
    def calculate(
        profit_loss: ProfitLossStatement,
        balance_sheet: BalanceSheet,
        working_capital_proj: WorkingCapitalProjection,
        cash_flow: CashFlowStatement,
    ) -> FinancialRatioSet:
        """
        Calculates all standard financial ratios for each projection year.
        """
        pl_map = {p.year: p for p in profit_loss.years}
        bs_map = {b.year: b for b in balance_sheet.years}
        wc_map = {w.year: w for w in working_capital_proj.years}
        cf_map = {c.year: c for c in cash_flow.years}

        ratio_years: List[FinancialRatioYear] = []

        def safe_div(num: Optional[float], den: Optional[float], scale: float = 1.0) -> Optional[float]:
            if num is None or den is None or den == 0.0:
                return None
            try:
                return round((num / den) * scale, 2)
            except (ZeroDivisionError, OverflowError):
                return None

        for y in range(1, len(profit_loss.years) + 1):
            pl = pl_map.get(y)
            bs = bs_map.get(y)
            wc = wc_map.get(y)
            cf = cf_map.get(y)

            rev = pl.revenue if pl else None
            cogs = pl.cogs if pl else None
            gp = pl.gross_profit if pl else None
            ebitda = pl.ebitda if pl else None
            ebit = pl.ebit if pl else None
            interest = pl.interest_expense if pl else None
            pat = pl.profit_after_tax if pl else None
            depr = pl.depreciation if (pl and pl.depreciation is not None) else None

            total_assets = bs.total_assets if bs else None
            total_equity = bs.total_equity if bs else None
            total_ca = bs.total_current_assets if bs else None
            total_cl = bs.trade_payables if bs else None
            term_debt = bs.term_loan_outstanding if bs else None
            inv = bs.inventory if bs else None
            rec = bs.trade_receivables if bs else None
            cash = bs.cash_and_bank if bs else None

            nwc = wc.net_working_capital if wc else None
            prin_repaid = cf.principal_repayment if (cf and cf.principal_repayment is not None) else None

            # 1. Profitability
            gm = safe_div(gp, rev, 100.0)
            ebitda_m = safe_div(ebitda, rev, 100.0)
            ebit_m = safe_div(ebit, rev, 100.0)
            npm = safe_div(pat, rev, 100.0)
            roa = safe_div(pat, total_assets, 100.0)
            roe = safe_div(pat, total_equity, 100.0)

            # 2. Liquidity
            # Zero current liabilities with known current assets → None (no ratio, not 10.0)
            curr_r = safe_div(total_ca, total_cl)
            quick_assets: Optional[float] = None
            if cash is not None and rec is not None:
                quick_assets = cash + rec
            elif cash is not None:
                quick_assets = cash
            elif rec is not None:
                quick_assets = rec
            quick_r = safe_div(quick_assets, total_cl)
            wc_ratio = safe_div(nwc, rev)

            # 3. Leverage
            de = safe_div(term_debt, total_equity)
            da = safe_div(term_debt, total_assets)
            # Zero interest with known EBIT → None (no meaningful coverage ratio)
            ic = safe_div(ebit, interest)

            # 4. Debt Service (DSCR)
            # DSCR = (PAT + Depr + Interest) / (Principal Repaid + Interest)
            dscr_val: Optional[float] = None
            if prin_repaid is not None and interest is not None and pat is not None and depr is not None:
                debt_service = prin_repaid + interest
                if debt_service > 0:
                    cf_available = pat + depr + interest
                    dscr_val = safe_div(cf_available, debt_service)
                else:
                    # Debt service is zero -> DSCR is not applicable (None)
                    dscr_val = None
            else:
                dscr_val = None

            # 5. Efficiency
            inv_d = safe_div(inv, cogs, 365.0)
            rec_d = safe_div(rec, rev, 365.0)
            pay_d = safe_div(total_cl, cogs, 365.0) if total_cl is not None else None

            ccc: Optional[float] = None
            if inv_d is not None and rec_d is not None and pay_d is not None:
                ccc = round(inv_d + rec_d - pay_d, 1)
            # If any component unknown → CCC stays None

            asset_to = safe_div(rev, total_assets)

            ratio_years.append(
                FinancialRatioYear(
                    year=y,
                    gross_margin=gm,
                    ebitda_margin=ebitda_m,
                    ebit_margin=ebit_m,
                    net_profit_margin=npm,
                    return_on_assets=roa,
                    return_on_equity=roe,
                    current_ratio=curr_r,
                    quick_ratio=quick_r,
                    working_capital_ratio=wc_ratio,
                    debt_to_equity=de,
                    debt_to_assets=da,
                    interest_coverage=ic,
                    dscr=dscr_val,
                    inventory_days=inv_d,
                    receivable_days=rec_d,
                    payable_days=pay_d,
                    cash_conversion_cycle=ccc,
                    asset_turnover=asset_to
                )
            )

        if not ratio_years:
            overall_status = "INSUFFICIENT_DATA"
        else:
            resolved_counts = []
            total_counts = []
            for ry in ratio_years:
                vals = [
                    ry.gross_margin, ry.ebitda_margin, ry.ebit_margin, ry.net_profit_margin,
                    ry.return_on_assets, ry.return_on_equity, ry.current_ratio, ry.quick_ratio,
                    ry.working_capital_ratio, ry.inventory_days, ry.receivable_days, ry.payable_days,
                    ry.cash_conversion_cycle, ry.asset_turnover
                ]
                if ry.debt_to_equity is not None or ry.dscr is not None:
                    vals.extend([ry.debt_to_equity, ry.debt_to_assets, ry.interest_coverage, ry.dscr])
                resolved_counts.append(sum(1 for v in vals if v is not None))
                total_counts.append(len(vals))

            total_resolved = sum(resolved_counts)
            total_expected = sum(total_counts)

            if total_resolved == 0:
                overall_status = "INSUFFICIENT_DATA"
            elif total_resolved == total_expected:
                overall_status = "RESOLVED"
            else:
                overall_status = "PARTIALLY_DERIVED"

        return FinancialRatioSet(
            status=overall_status,
            years=ratio_years,
            notes="Institutional financial ratios calculated with strict zero-division protection."
        )


financial_ratios_engine = FinancialRatiosEngine()
