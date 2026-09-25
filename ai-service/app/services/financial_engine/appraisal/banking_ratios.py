"""
Banking Ratios & Investment Return Metrics Engine for M4 Banking Appraisal.
Deterministically computes Interest Coverage Ratio (ICR), Internal Rate of Return (IRR),
Net Present Value (NPV), and Payback Period.
Strict rules:
- ICR handles zero interest and zero/negative denominators cleanly without division-by-zero.
- NPV NEVER invents a discount rate. If discount rate is missing, returns None with MISSING_DISCOUNT_RATE.
- IRR and Payback require fully resolved cash flows; never calculates from fabricated defaults.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    ICRYear,
    BankingRatiosResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    ProfitLossStatement,
    CashFlowStatement,
    FundingSourcesUses,
    ProjectCostAnalysis
)


def _compute_irr(cash_flows: List[float], max_iter: int = 100, tol: float = 1e-6) -> Optional[float]:
    """
    Deterministic IRR solver using bisection and Newton-Raphson.
    Requires at least one negative and one positive cash flow.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None

    has_neg = any(cf < 0 for cf in cash_flows)
    has_pos = any(cf > 0 for cf in cash_flows)
    if not (has_neg and has_pos):
        return None

    # Bisection search over range [-0.90, 5.0]
    def npv_func(r: float) -> float:
        val = 0.0
        for t, cf in enumerate(cash_flows):
            val += cf / ((1.0 + r) ** t)
        return val

    low = -0.90
    high = 5.0
    f_low = npv_func(low)
    f_high = npv_func(high)

    if f_low * f_high > 0:
        # Check if root lies within extended range or no standard single IRR exists
        return None

    for _ in range(max_iter):
        mid = (low + high) / 2.0
        f_mid = npv_func(mid)
        if abs(f_mid) < tol:
            return round(mid * 100.0, 2)
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    return round(((low + high) / 2.0) * 100.0, 2)


class BankingRatiosEngine:
    """
    Deterministic banking ratios and return metrics engine.
    """

    def evaluate(
        self,
        profit_loss: Optional[ProfitLossStatement] = None,
        cash_flow: Optional[CashFlowStatement] = None,
        sources_uses: Optional[FundingSourcesUses] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        discount_rate: Optional[float] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> BankingRatiosResult:
        prov = provenance or ProvenanceBuilder()

        # ---------------------------------------------------------------------
        # 1. Interest Coverage Ratio (ICR = EBIT / Interest Expense)
        # ---------------------------------------------------------------------
        icr_years: List[ICRYear] = []
        valid_icrs: List[float] = []
        icr_status = AppraisalStatus.RESOLVED

        if profit_loss and profit_loss.years:
            for pl_y in profit_loss.years:
                ebit = pl_y.ebit
                interest = pl_y.interest_expense

                if ebit is None or interest is None:
                    icr_years.append(ICRYear(
                        year=pl_y.year,
                        ebit=ebit,
                        interest_expense=interest,
                        icr=None,
                        status=AppraisalStatus.UNRESOLVED,
                        reason_code=ReasonCode.INSUFFICIENT_DATA
                    ))
                    icr_status = AppraisalStatus.PARTIALLY_DERIVED
                elif interest == 0.0:
                    # Enterprise with zero interest
                    icr_years.append(ICRYear(
                        year=pl_y.year,
                        ebit=ebit,
                        interest_expense=0.0,
                        icr=None,
                        status=AppraisalStatus.RESOLVED,
                        reason_code=ReasonCode.NOT_APPLICABLE_ZERO_INTEREST
                    ))
                elif interest < 0.0:
                    icr_years.append(ICRYear(
                        year=pl_y.year,
                        ebit=ebit,
                        interest_expense=interest,
                        icr=None,
                        status=AppraisalStatus.UNRESOLVED,
                        reason_code=ReasonCode.NEGATIVE_DENOMINATOR
                    ))
                else:
                    icr_val = round(ebit / interest, 2)
                    icr_years.append(ICRYear(
                        year=pl_y.year,
                        ebit=ebit,
                        interest_expense=interest,
                        icr=icr_val,
                        status=AppraisalStatus.RESOLVED
                    ))
                    valid_icrs.append(icr_val)
        else:
            icr_status = AppraisalStatus.UNRESOLVED

        avg_icr = round(sum(valid_icrs) / len(valid_icrs), 2) if valid_icrs else None
        min_icr = min(valid_icrs) if valid_icrs else None

        if avg_icr is not None:
            prov.record(
                metric="average_icr",
                value=avg_icr,
                source=MetricSource.DERIVED,
                source_reference="ProfitLossStatement (EBIT / Interest)",
                calculation_method="Average Interest Coverage Ratio",
                status=AppraisalStatus.RESOLVED,
                dependencies=["profit_loss_statement"]
            )

        # ---------------------------------------------------------------------
        # 2. Return Metrics (IRR, NPV, Payback Period)
        # ---------------------------------------------------------------------
        irr_val: Optional[float] = None
        npv_val: Optional[float] = None
        payback_val: Optional[float] = None
        ret_status = AppraisalStatus.RESOLVED
        ret_notes = None
        ret_rc = None

        # Build Project Cash Flow Stream
        # Year 0: Negative Initial Investment Outflow
        initial_investment: Optional[float] = None
        if sources_uses and sources_uses.total_uses and sources_uses.total_uses > 0:
            initial_investment = sources_uses.total_uses
        elif project_cost_analysis and project_cost_analysis.total_project_cost and project_cost_analysis.total_project_cost > 0:
            initial_investment = project_cost_analysis.total_project_cost

        resolved_annual_cfs: List[float] = []
        cfs_incomplete = False

        if cash_flow and cash_flow.years:
            for cf_y in cash_flow.years:
                if cf_y.cash_from_operations is not None:
                    resolved_annual_cfs.append(cf_y.cash_from_operations)
                else:
                    cfs_incomplete = True
                    break
        else:
            cfs_incomplete = True

        if initial_investment is None or cfs_incomplete or not resolved_annual_cfs:
            ret_status = AppraisalStatus.INSUFFICIENT_DATA
            ret_rc = ReasonCode.MISSING_CASH_FLOWS
            ret_notes = "Insufficient resolved cash flow data for investment return appraisal."
        else:
            # Full cash flow series: [ -initial_investment, CF_1, CF_2, ... ]
            full_cfs = [-initial_investment] + resolved_annual_cfs

            # A. IRR
            irr_val = _compute_irr(full_cfs)
            if irr_val is not None:
                prov.record(
                    metric="irr",
                    value=irr_val,
                    source=MetricSource.DERIVED,
                    source_reference="Cash Flow from Operations (FCFF basis)",
                    calculation_method="Deterministic Bisection IRR on fully resolved cash flows",
                    status=AppraisalStatus.RESOLVED,
                    dependencies=["cash_flow_statement", "sources_uses"]
                )

            # B. NPV (Only when discount rate is explicitly provided)
            if discount_rate is not None and discount_rate > 0.0:
                calc_npv = 0.0
                for t, cf in enumerate(full_cfs):
                    calc_npv += cf / ((1.0 + discount_rate) ** t)
                npv_val = round(calc_npv, 2)
                prov.record(
                    metric="npv",
                    value=npv_val,
                    source=MetricSource.DERIVED,
                    source_reference=f"Cash Flow from Operations (FCFF basis) discounted at {discount_rate*100:.1f}%",
                    calculation_method="Sum of discounted cash flows",
                    status=AppraisalStatus.RESOLVED,
                    dependencies=["cash_flow_statement", "discount_rate"]
                )
            else:
                # NPV unresolved because discount rate was not supplied
                npv_val = None
                ret_rc = ReasonCode.MISSING_DISCOUNT_RATE
                ret_notes = "NPV unresolved: Discount rate must be explicitly supplied (MISSING_DISCOUNT_RATE)."

            # C. Payback Period
            cum_cf = -initial_investment
            for idx, cf in enumerate(resolved_annual_cfs, start=1):
                prev_cum = cum_cf
                cum_cf += cf
                if cum_cf >= 0.0:
                    # Interpolate fraction of year
                    fraction = abs(prev_cum) / cf if cf > 0 else 0.0
                    payback_val = round((idx - 1) + fraction, 2)
                    break

            if payback_val is not None:
                prov.record(
                    metric="payback_period_years",
                    value=payback_val,
                    source=MetricSource.DERIVED,
                    source_reference="Cumulative Cash Flow from Operations",
                    calculation_method="Cumulative Payback Interpolation",
                    status=AppraisalStatus.RESOLVED,
                    dependencies=["cash_flow_statement"]
                )

            # Return metrics status:
            if npv_val is None:
                if irr_val is not None or payback_val is not None:
                    ret_status = AppraisalStatus.PARTIALLY_DERIVED
                else:
                    ret_status = AppraisalStatus.UNRESOLVED
            else:
                ret_status = AppraisalStatus.RESOLVED

        # Overall status must reflect both ICR status and return_metrics status
        if icr_status == AppraisalStatus.RESOLVED and ret_status == AppraisalStatus.RESOLVED:
            overall_status = AppraisalStatus.RESOLVED
        elif (
            icr_status in (AppraisalStatus.RESOLVED, AppraisalStatus.PARTIALLY_DERIVED)
            or ret_status in (AppraisalStatus.RESOLVED, AppraisalStatus.PARTIALLY_DERIVED)
        ):
            overall_status = AppraisalStatus.PARTIALLY_DERIVED
        elif ret_status == AppraisalStatus.INSUFFICIENT_DATA or icr_status == AppraisalStatus.INSUFFICIENT_DATA:
            overall_status = AppraisalStatus.INSUFFICIENT_DATA
        else:
            overall_status = AppraisalStatus.UNRESOLVED

        return BankingRatiosResult(
            status=overall_status,
            icr_years=icr_years,
            average_icr=avg_icr,
            minimum_icr=min_icr,
            irr=irr_val,
            npv=npv_val,
            discount_rate=discount_rate,
            payback_period_years=payback_val,
            return_metrics_status=ret_status,
            return_metrics_notes=ret_notes,
            reason_code=ret_rc
        )


banking_ratios_engine = BankingRatiosEngine()
