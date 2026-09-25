"""
Liquidity Analysis Engine for M4 Banking Appraisal.
Deterministically computes year-wise Current Ratio, Quick Ratio, Working Capital,
Operating Cash Flow Coverage, and Cash Buffer Adequacy.
Strict rule: Does not assume inventory, receivables, payables, or cash are zero unless explicitly zero upstream.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    LiquidityYear,
    LiquidityAnalysisResult,
    DebtServiceAnalysisResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.constants import (
    LIQUIDITY_CURRENT_RATIO_ADEQUATE,
    LIQUIDITY_CURRENT_RATIO_TIGHT
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    BalanceSheet,
    WorkingCapitalProjection,
    CashFlowStatement,
    ProfitLossStatement
)


class LiquidityAnalysisEngine:
    """
    Deterministic liquidity appraisal engine.
    """

    def evaluate(
        self,
        balance_sheet: Optional[BalanceSheet] = None,
        working_capital_proj: Optional[WorkingCapitalProjection] = None,
        cash_flow: Optional[CashFlowStatement] = None,
        profit_loss: Optional[ProfitLossStatement] = None,
        debt_service: Optional[DebtServiceAnalysisResult] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> LiquidityAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        if not balance_sheet or not balance_sheet.years:
            return LiquidityAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                average_current_ratio=None,
                average_quick_ratio=None,
                minimum_cash_buffer_months=None,
                working_capital_adequacy="UNRESOLVED",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        cf_years_map = {y.year: y for y in cash_flow.years} if cash_flow and cash_flow.years else {}
        pl_years_map = {y.year: y for y in profit_loss.years} if profit_loss and profit_loss.years else {}
        ds_years_map = {y.year: y for y in debt_service.years} if debt_service and debt_service.years else {}

        years: List[LiquidityYear] = []
        valid_cr: List[float] = []
        valid_qr: List[float] = []
        valid_buffers: List[float] = []
        has_unresolved = False

        for bs_y in balance_sheet.years:
            ca = bs_y.total_current_assets
            # Strict non-fabrication: If trade_payables is known but other_current_liabilities is None,
            # current liabilities must remain None. Explicit 0.0 remains 0.0.
            if bs_y.trade_payables is None or bs_y.other_current_liabilities is None:
                cl = None
            else:
                cl = round(bs_y.trade_payables + bs_y.other_current_liabilities, 2)

            inv = bs_y.inventory
            cash = bs_y.cash_and_bank

            cf_y = cf_years_map.get(bs_y.year)
            pl_y = pl_years_map.get(bs_y.year)
            ds_y = ds_years_map.get(bs_y.year)

            # 1. Current Ratio
            cr_val = None
            rc = None
            if ca is None or cl is None:
                has_unresolved = True
                rc = ReasonCode.INSUFFICIENT_DATA
            elif cl == 0.0:
                if ca == 0.0:
                    cr_val = None
                    rc = ReasonCode.NOT_APPLICABLE
                else:
                    cr_val = None
                    rc = ReasonCode.ZERO_DENOMINATOR
            elif cl < 0.0:
                cr_val = None
                rc = ReasonCode.NEGATIVE_DENOMINATOR
            else:
                cr_val = round(ca / cl, 2)
                valid_cr.append(cr_val)

            # 2. Quick Ratio
            qr_val = None
            if ca is not None and cl is not None and cl > 0 and inv is not None:
                quick_assets = ca - inv
                qr_val = round(quick_assets / cl, 2)
                valid_qr.append(qr_val)

            # 3. Net Working Capital
            nwc = round(ca - cl, 2) if (ca is not None and cl is not None) else None

            # 4. Operating Cash Flow Coverage
            ocf_cov = None
            if cf_y and cf_y.cash_from_operations is not None and cl is not None and cl > 0:
                ocf_cov = round(cf_y.cash_from_operations / cl, 2)

            # 5. Cash Buffer Months
            cash_buf = None
            if cash is not None and pl_y and pl_y.operating_expenses is not None and pl_y.operating_expenses > 0:
                monthly_opex = pl_y.operating_expenses / 12.0
                cash_buf = round(cash / monthly_opex, 2)
                valid_buffers.append(cash_buf)

            # 6. Debt Service Liquidity Ratio (Strict: never convert missing cash/OCF to 0)
            ds_liq = None
            if ds_y and ds_y.total_debt_service and ds_y.total_debt_service > 0:
                if cash is not None and cf_y and cf_y.cash_from_operations is not None:
                    available_liq = round(cash + cf_y.cash_from_operations, 2)
                    ds_liq = round(available_liq / ds_y.total_debt_service, 2)

            y_status = AppraisalStatus.RESOLVED if cr_val is not None else AppraisalStatus.UNRESOLVED

            years.append(LiquidityYear(
                year=bs_y.year,
                current_assets=ca,
                current_liabilities=cl,
                current_ratio=cr_val,
                quick_ratio=qr_val,
                working_capital=nwc,
                operating_cash_flow_coverage=ocf_cov,
                cash_buffer_months=cash_buf,
                debt_service_liquidity_ratio=ds_liq,
                status=y_status,
                reason_code=rc
            ))

        avg_cr = round(sum(valid_cr) / len(valid_cr), 2) if valid_cr else None
        avg_qr = round(sum(valid_qr) / len(valid_qr), 2) if valid_qr else None
        min_buf = min(valid_buffers) if valid_buffers else None

        # Adequacy assessment using centralized thresholds
        if avg_cr is not None and avg_cr >= LIQUIDITY_CURRENT_RATIO_ADEQUATE:
            wc_assess = "ADEQUATE"
        elif avg_cr is not None and avg_cr >= LIQUIDITY_CURRENT_RATIO_TIGHT:
            wc_assess = "TIGHT"
        elif avg_cr is not None:
            wc_assess = "INSUFFICIENT"
        else:
            wc_assess = "UNRESOLVED"

        prov.record(
            metric="average_current_ratio",
            value=avg_cr,
            source=MetricSource.DERIVED,
            source_reference="BalanceSheet (Current Assets / Current Liabilities)",
            calculation_method="Average annual Current Ratio",
            status=AppraisalStatus.RESOLVED if avg_cr is not None else AppraisalStatus.UNRESOLVED,
            dependencies=["balance_sheet"]
        )

        if not valid_cr:
            overall_status = AppraisalStatus.UNRESOLVED
        elif has_unresolved:
            overall_status = AppraisalStatus.PARTIALLY_DERIVED
        else:
            overall_status = AppraisalStatus.RESOLVED

        return LiquidityAnalysisResult(
            status=overall_status,
            years=years,
            average_current_ratio=avg_cr,
            average_quick_ratio=avg_qr,
            minimum_cash_buffer_months=min_buf,
            working_capital_adequacy=wc_assess,
            reason_code=ReasonCode.INSUFFICIENT_DATA if not valid_cr else None
        )


liquidity_analysis_engine = LiquidityAnalysisEngine()
