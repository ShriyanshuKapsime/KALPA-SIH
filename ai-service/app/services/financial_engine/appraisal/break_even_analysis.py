"""
Break-Even Analysis Engine for M4 Banking Appraisal.
Deterministically computes contribution margin, break-even sales, break-even utilization,
and margin of safety across projection years, and reconciles with Stage 9 break-even.
Strict rule: Never invents contribution margins or handles unresolved costs as zero.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    BreakEvenYear,
    BreakEvenAnalysisResult,
    AppraisalStatus,
    ValidationState,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    ProfitLossStatement,
    CostProjection,
    BreakEvenAnalysis
)


class BreakEvenAnalysisEngine:
    """
    Deterministic contribution-based break-even analysis engine.
    """

    def evaluate(
        self,
        profit_loss: Optional[ProfitLossStatement] = None,
        cost_projection: Optional[CostProjection] = None,
        stage9_break_even: Optional[BreakEvenAnalysis] = None,
        fixed_cost_ratio: Optional[float] = None,
        tolerance_pct: float = 15.0,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> BreakEvenAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        # If fixed/variable split is not explicitly provided, break-even is UNRESOLVED
        if fixed_cost_ratio is None:
            return BreakEvenAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                year1_break_even_sales=None,
                year1_break_even_utilization_pct=None,
                year1_margin_of_safety_pct=None,
                stage9_break_even_sales=stage9_break_even.annual_break_even_revenue if stage9_break_even else None,
                stage9_break_even_utilization_pct=stage9_break_even.break_even_utilization_pct if stage9_break_even else None,
                reconciliation_status=ValidationState.UNRESOLVED,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        fixed_ratio = max(0.0, min(1.0, fixed_cost_ratio))
        var_ratio = 1.0 - fixed_ratio

        if not profit_loss or not profit_loss.years:
            return BreakEvenAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                year1_break_even_sales=None,
                year1_break_even_utilization_pct=None,
                year1_margin_of_safety_pct=None,
                stage9_break_even_sales=stage9_break_even.annual_break_even_revenue if stage9_break_even else None,
                stage9_break_even_utilization_pct=stage9_break_even.break_even_utilization_pct if stage9_break_even else None,
                reconciliation_status=ValidationState.UNRESOLVED,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        years: List[BreakEvenYear] = []
        has_unresolved = False

        for pl_y in profit_loss.years:
            rev = pl_y.revenue
            cogs = pl_y.cogs
            opex = pl_y.operating_expenses

            if rev is None or cogs is None or opex is None:
                has_unresolved = True
                years.append(BreakEvenYear(
                    year=pl_y.year,
                    revenue=rev,
                    fixed_costs=None,
                    variable_costs=None,
                    contribution_margin=None,
                    contribution_margin_ratio=None,
                    break_even_sales=None,
                    break_even_utilization_pct=None,
                    margin_of_safety_pct=None,
                    status=AppraisalStatus.UNRESOLVED,
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))
                continue

            if rev <= 0:
                years.append(BreakEvenYear(
                    year=pl_y.year,
                    revenue=rev,
                    fixed_costs=round(opex * fixed_ratio, 2),
                    variable_costs=round(cogs + (opex * var_ratio), 2),
                    contribution_margin=round(rev - cogs, 2),
                    contribution_margin_ratio=None,
                    break_even_sales=None,
                    break_even_utilization_pct=None,
                    margin_of_safety_pct=None,
                    status=AppraisalStatus.NOT_APPLICABLE,
                    reason_code=ReasonCode.ZERO_DENOMINATOR
                ))
                continue

            var_costs = round(cogs + (opex * var_ratio), 2)
            fixed_costs = round(opex * fixed_ratio, 2)
            contrib = rev - var_costs
            cm_ratio = contrib / rev

            if cm_ratio <= 0:
                # Negative contribution margin -> business cannot break even
                years.append(BreakEvenYear(
                    year=pl_y.year,
                    revenue=round(rev, 2),
                    fixed_costs=round(fixed_costs, 2),
                    variable_costs=round(var_costs, 2),
                    contribution_margin=round(contrib, 2),
                    contribution_margin_ratio=round(cm_ratio, 4),
                    break_even_sales=None,
                    break_even_utilization_pct=None,
                    margin_of_safety_pct=0.0,
                    status=AppraisalStatus.RESOLVED,
                    reason_code=ReasonCode.NEGATIVE_PROFITABILITY
                ))
                continue

            be_sales = round(fixed_costs / cm_ratio, 2)
            be_util = round((be_sales / rev) * 100.0, 2)
            mos = round(max(0.0, 100.0 - be_util), 2)

            years.append(BreakEvenYear(
                year=pl_y.year,
                revenue=round(rev, 2),
                fixed_costs=round(fixed_costs, 2),
                variable_costs=round(var_costs, 2),
                contribution_margin=round(contrib, 2),
                contribution_margin_ratio=round(cm_ratio, 4),
                break_even_sales=be_sales,
                break_even_utilization_pct=be_util,
                margin_of_safety_pct=mos,
                status=AppraisalStatus.RESOLVED
            ))

        y1 = years[0] if years else None
        y1_be_sales = y1.break_even_sales if y1 else None
        y1_be_util = y1.break_even_utilization_pct if y1 else None
        y1_mos = y1.margin_of_safety_pct if y1 else None

        st9_sales = stage9_break_even.annual_break_even_revenue if stage9_break_even else None
        st9_util = stage9_break_even.break_even_utilization_pct if stage9_break_even else None

        recon_status = ValidationState.PASSED
        recon_diff = None
        recon_code = None

        if st9_util is not None and y1_be_util is not None:
            recon_diff = round(y1_be_util - st9_util, 2)
            if abs(recon_diff) > tolerance_pct:
                recon_status = ValidationState.FAILED
                recon_code = ReasonCode.STAGE9_BREAK_EVEN_MISMATCH
            else:
                recon_status = ValidationState.PASSED
                recon_code = ReasonCode.STAGE9_RECONCILIATION_PASSED
        elif st9_util is not None or y1_be_util is not None:
            recon_status = ValidationState.UNRESOLVED

        prov.record(
            metric="year1_break_even_sales",
            value=y1_be_sales,
            source=MetricSource.DERIVED,
            source_reference="ProfitLossStatement Year 1",
            calculation_method="Fixed Costs / Contribution Margin Ratio",
            status=y1.status if y1 else AppraisalStatus.UNRESOLVED,
            dependencies=["profit_loss_statement"]
        )

        overall_status = AppraisalStatus.UNRESOLVED if (has_unresolved and not y1_be_sales) else (
            AppraisalStatus.PARTIALLY_DERIVED if has_unresolved else AppraisalStatus.RESOLVED
        )

        return BreakEvenAnalysisResult(
            status=overall_status,
            years=years,
            year1_break_even_sales=y1_be_sales,
            year1_break_even_utilization_pct=y1_be_util,
            year1_margin_of_safety_pct=y1_mos,
            stage9_break_even_sales=st9_sales,
            stage9_break_even_utilization_pct=st9_util,
            reconciliation_status=recon_status,
            reconciliation_difference=recon_diff,
            reason_code=recon_code
        )


break_even_analysis_engine = BreakEvenAnalysisEngine()
