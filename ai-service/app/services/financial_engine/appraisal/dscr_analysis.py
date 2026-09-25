"""
DSCR & ADSCR Analysis Engine for M4 Banking Appraisal.
Deterministically computes year-wise DSCR, Minimum DSCR, Average DSCR (ADSCR),
coverage trend, and reconciles against authoritative Stage 9 DSCR.
Strict rule: Does not manufacture DSCR when numerator or denominator is unresolved.
"""
from typing import List, Optional, Tuple
from app.services.financial_engine.appraisal.appraisal_schema import (
    DSCRYear,
    DSCRAnalysisResult,
    RepaymentCapacityResult,
    DebtServiceAnalysisResult,
    AppraisalStatus,
    ValidationState,
    MetricSource,
    CoverageTrend
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import DebtServiceAnalysis


class DSCRAnalysisEngine:
    """
    Deterministic DSCR & ADSCR appraisal engine with Stage 9 reconciliation.
    """

    def evaluate(
        self,
        repayment_capacity: RepaymentCapacityResult,
        debt_service: DebtServiceAnalysisResult,
        stage9_debt_service: Optional[DebtServiceAnalysis] = None,
        tolerance: float = 0.20,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> DSCRAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        # Handle unresolved inputs
        if repayment_capacity.status == AppraisalStatus.UNRESOLVED or debt_service.status == AppraisalStatus.UNRESOLVED:
            return DSCRAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                minimum_dscr=None,
                average_dscr=None,
                trend=CoverageTrend.NOT_APPLICABLE,
                stage9_dscr=stage9_debt_service.dscr if stage9_debt_service else None,
                reconciliation_status=ValidationState.UNRESOLVED,
                reconciliation_difference=None,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        # Handle zero debt
        if debt_service.is_zero_debt:
            years: List[DSCRYear] = []
            for y_cap in repayment_capacity.years:
                years.append(DSCRYear(
                    year=y_cap.year,
                    dscr=None,
                    cads=y_cap.cash_available_for_debt_service,
                    debt_service=0.0,
                    status=AppraisalStatus.NOT_APPLICABLE,
                    source=MetricSource.DERIVED,
                    calculation_method="Not applicable: zero debt service obligation",
                    reason_code=ReasonCode.ZERO_DEBT
                ))
            prov.record(
                metric="average_dscr",
                value=None,
                source=MetricSource.DERIVED,
                source_reference="repayment_capacity (Zero Debt)",
                calculation_method="Not applicable for zero debt enterprise",
                status=AppraisalStatus.NOT_APPLICABLE
            )
            return DSCRAnalysisResult(
                status=AppraisalStatus.NOT_APPLICABLE,
                years=years,
                minimum_dscr=None,
                average_dscr=None,
                trend=CoverageTrend.NOT_APPLICABLE,
                stage9_dscr=stage9_debt_service.dscr if stage9_debt_service else None,
                reconciliation_status=ValidationState.PASSED,
                reconciliation_difference=0.0,
                reason_code=ReasonCode.ZERO_DEBT
            )

        years = []
        valid_dscrs: List[float] = []
        has_unresolved = False

        for y_cap in repayment_capacity.years:
            cads = y_cap.cash_available_for_debt_service
            ds = y_cap.debt_service_obligation

            if cads is None or ds is None:
                has_unresolved = True
                years.append(DSCRYear(
                    year=y_cap.year,
                    dscr=None,
                    cads=cads,
                    debt_service=ds,
                    status=AppraisalStatus.UNRESOLVED,
                    source=MetricSource.DERIVED,
                    calculation_method="CADS / (Principal + Interest)",
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))
            elif ds <= 0.0:
                # Year with no debt service (e.g. loan fully repaid in year 4, 5)
                years.append(DSCRYear(
                    year=y_cap.year,
                    dscr=None,
                    cads=cads,
                    debt_service=0.0,
                    status=AppraisalStatus.NOT_APPLICABLE,
                    source=MetricSource.DERIVED,
                    calculation_method="Post-amortization period (zero debt service)",
                    reason_code=ReasonCode.ZERO_DEBT
                ))
            else:
                d_val = round(cads / ds, 2)
                years.append(DSCRYear(
                    year=y_cap.year,
                    dscr=d_val,
                    cads=cads,
                    debt_service=ds,
                    status=AppraisalStatus.RESOLVED,
                    source=MetricSource.DERIVED,
                    calculation_method="CADS / (Principal + Interest)"
                ))
                valid_dscrs.append(d_val)

        if not valid_dscrs:
            return DSCRAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=years,
                minimum_dscr=None,
                average_dscr=None,
                trend=CoverageTrend.NOT_APPLICABLE,
                stage9_dscr=stage9_debt_service.dscr if stage9_debt_service else None,
                reconciliation_status=ValidationState.UNRESOLVED,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        min_dscr = min(valid_dscrs)
        avg_dscr = round(sum(valid_dscrs) / len(valid_dscrs), 2)

        # Determine trend
        if len(valid_dscrs) >= 2:
            first_half = sum(valid_dscrs[:len(valid_dscrs)//2]) / (len(valid_dscrs)//2)
            second_half = sum(valid_dscrs[len(valid_dscrs)//2:]) / (len(valid_dscrs) - len(valid_dscrs)//2)
            if second_half - first_half > 0.15:
                trend = CoverageTrend.IMPROVING
            elif first_half - second_half > 0.15:
                trend = CoverageTrend.DETERIORATING
            else:
                trend = CoverageTrend.STABLE
        else:
            trend = CoverageTrend.STABLE

        # Stage 9 Reconciliation
        st9_dscr = stage9_debt_service.dscr if stage9_debt_service else None
        recon_status = ValidationState.PASSED
        recon_diff = None
        recon_code = None

        if st9_dscr is not None:
            # Stage 9 DSCR evaluates average repayment quarters across the loan
            comp_dscr = avg_dscr if avg_dscr is not None else (years[0].dscr if years and years[0].dscr is not None else None)
            if comp_dscr is not None:
                recon_diff = round(comp_dscr - st9_dscr, 2)
                effective_tol = max(tolerance, st9_dscr * 0.15)
                if abs(recon_diff) > effective_tol:
                    recon_status = ValidationState.FAILED
                    recon_code = ReasonCode.STAGE9_RECONCILIATION_FAILED
                else:
                    recon_status = ValidationState.PASSED
                    recon_code = ReasonCode.STAGE9_RECONCILIATION_PASSED

        prov.record(
            metric="average_dscr",
            value=avg_dscr,
            source=MetricSource.DERIVED,
            source_reference="repayment_capacity",
            calculation_method="Average annual DSCR over projection horizon",
            status=AppraisalStatus.RESOLVED if not has_unresolved else AppraisalStatus.PARTIALLY_DERIVED,
            dependencies=["repayment_capacity", "debt_service"]
        )

        return DSCRAnalysisResult(
            status=AppraisalStatus.RESOLVED if not has_unresolved else AppraisalStatus.PARTIALLY_DERIVED,
            years=years,
            minimum_dscr=min_dscr,
            average_dscr=avg_dscr,
            trend=trend,
            stage9_dscr=st9_dscr,
            reconciliation_status=recon_status,
            reconciliation_difference=recon_diff,
            reason_code=recon_code
        )


dscr_analysis_engine = DSCRAnalysisEngine()
