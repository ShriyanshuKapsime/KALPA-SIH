"""
Repayment Capacity Analysis Engine for M4 Banking Appraisal.
Evaluates Cash Available for Debt Service (CADS), annual debt obligations,
surplus/deficit buffers, and capacity ratios deterministically.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    RepaymentCapacityYear,
    RepaymentCapacityResult,
    DebtServiceAnalysisResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import ProfitLossStatement, CashFlowStatement


class RepaymentCapacityEngine:
    """
    Deterministic repayment capacity evaluation engine.
    """

    def evaluate(
        self,
        debt_service: DebtServiceAnalysisResult,
        profit_loss: Optional[ProfitLossStatement] = None,
        cash_flow: Optional[CashFlowStatement] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> RepaymentCapacityResult:
        prov = provenance or ProvenanceBuilder()

        if debt_service.status != AppraisalStatus.RESOLVED:
            return RepaymentCapacityResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                total_cads=None,
                total_debt_service=None,
                cumulative_surplus_deficit=None,
                minimum_capacity_ratio=None,
                capacity_assessment="UNRESOLVED",
                reason_code=ReasonCode.MISSING_DEBT_SERVICE
            )

        if not profit_loss or not profit_loss.years:
            return RepaymentCapacityResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                total_cads=None,
                total_debt_service=None,
                cumulative_surplus_deficit=None,
                minimum_capacity_ratio=None,
                capacity_assessment="UNRESOLVED",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        pl_years_map = {y.year: y for y in profit_loss.years}
        years: List[RepaymentCapacityYear] = []

        total_cads = 0.0
        total_ds = 0.0
        min_ratio: Optional[float] = None
        has_unresolved_year = False

        for ds_year in debt_service.years:
            y_idx = ds_year.year
            pl_y = pl_years_map.get(y_idx)

            # Require explicit non-None inputs (depreciation, interest, PAT, and debt service)
            # Never convert missing/None into 0.0
            is_int_missing = (not debt_service.is_zero_debt) and (pl_y.interest_expense is None)
            cash_op = pl_y.profit_after_tax if (pl_y and pl_y.profit_after_tax is not None) else (
                (pl_y.profit_before_tax if pl_y.profit_before_tax is not None else pl_y.ebitda) if pl_y else None
            )
            if (
                pl_y is None
                or cash_op is None
                or pl_y.depreciation is None
                or is_int_missing
                or ds_year.total_debt_service is None
            ):
                has_unresolved_year = True
                years.append(RepaymentCapacityYear(
                    year=y_idx,
                    cash_available_for_debt_service=None,
                    debt_service_obligation=ds_year.total_debt_service,
                    surplus_deficit=None,
                    capacity_ratio=None,
                    status=AppraisalStatus.UNRESOLVED,
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))
                continue

            pat = cash_op
            depr = pl_y.depreciation
            interest = 0.0 if debt_service.is_zero_debt else pl_y.interest_expense
            cads = round(pat + depr + interest, 2)
            ds = ds_year.total_debt_service

            surplus = round(cads - ds, 2)

            if ds == 0.0:
                ratio = None
                rc = ReasonCode.ZERO_DEBT
            elif ds > 0.0:
                ratio = round(cads / ds, 2)
                rc = None
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
            else:
                ratio = None
                rc = ReasonCode.ZERO_DENOMINATOR

            years.append(RepaymentCapacityYear(
                year=y_idx,
                cash_available_for_debt_service=cads,
                debt_service_obligation=ds,
                surplus_deficit=surplus,
                capacity_ratio=ratio,
                status=AppraisalStatus.RESOLVED,
                reason_code=rc
            ))

            total_cads += cads
            total_ds += ds

        if has_unresolved_year:
            return RepaymentCapacityResult(
                status=AppraisalStatus.UNRESOLVED,
                years=years,
                total_cads=None,
                total_debt_service=None,
                cumulative_surplus_deficit=None,
                minimum_capacity_ratio=None,
                capacity_assessment="UNRESOLVED",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        cum_surplus = round(total_cads - total_ds, 2)

        # Assessment classification
        if debt_service.is_zero_debt:
            assessment = "STRONG_ZERO_DEBT"
        elif min_ratio is not None and min_ratio >= 1.30:
            assessment = "ROBUST"
        elif min_ratio is not None and min_ratio >= 1.15:
            assessment = "ADEQUATE"
        elif min_ratio is not None and min_ratio >= 1.0:
            assessment = "TIGHT"
        else:
            assessment = "INSUFFICIENT"

        prov.record(
            metric="total_cads",
            value=round(total_cads, 2),
            source=MetricSource.DERIVED,
            source_reference="ProfitLossStatement (PAT + Depreciation + Interest)",
            calculation_method="Sum of annual CADS",
            status=AppraisalStatus.RESOLVED
        )

        return RepaymentCapacityResult(
            status=AppraisalStatus.RESOLVED,
            years=years,
            total_cads=round(total_cads, 2),
            total_debt_service=round(total_ds, 2),
            cumulative_surplus_deficit=cum_surplus,
            minimum_capacity_ratio=min_ratio,
            capacity_assessment=assessment
        )


repayment_capacity_engine = RepaymentCapacityEngine()
