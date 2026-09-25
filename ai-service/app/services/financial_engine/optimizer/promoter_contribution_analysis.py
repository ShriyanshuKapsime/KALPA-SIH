"""
Promoter Contribution Analysis for Milestone 5.
Evaluates promoter capital against required scheme margins.
Zero arbitrary defaults: never silently assumes 10%. Explicit zero remains zero.
"""
from typing import Optional
from app.services.financial_engine.optimizer.m5_schema import PromoterContributionAnalysisResult
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder


class PromoterContributionAnalysisEngine:
    """
    Evaluates promoter contribution adequacy against authoritative scheme margin requirements.
    """

    def evaluate(
        self,
        total_project_cost: Optional[float],
        available_promoter_contribution: Optional[float],
        scheme_margin_percentage: Optional[float],
        provenance: Optional[M5ProvenanceBuilder] = None
    ) -> PromoterContributionAnalysisResult:
        prov = provenance or M5ProvenanceBuilder()

        # If project cost is missing or <= 0
        if total_project_cost is None or total_project_cost <= 0:
            return PromoterContributionAnalysisResult(
                total_project_cost=None,
                available_promoter_contribution=available_promoter_contribution,
                required_promoter_contribution=None,
                required_percentage=scheme_margin_percentage,
                actual_percentage=None,
                gap_surplus=None,
                is_adequate=None,
                status="UNRESOLVED",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            )

        # If scheme margin requirement is not available
        if scheme_margin_percentage is None:
            return PromoterContributionAnalysisResult(
                total_project_cost=total_project_cost,
                available_promoter_contribution=available_promoter_contribution,
                required_promoter_contribution=None,
                required_percentage=None,
                actual_percentage=None,
                gap_surplus=None,
                is_adequate=None,
                status="UNRESOLVED",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            )

        # If available promoter contribution is unresolved
        if available_promoter_contribution is None:
            req_amount = round(total_project_cost * (scheme_margin_percentage / 100.0), 2)
            return PromoterContributionAnalysisResult(
                total_project_cost=total_project_cost,
                available_promoter_contribution=None,
                required_promoter_contribution=req_amount,
                required_percentage=scheme_margin_percentage,
                actual_percentage=None,
                gap_surplus=None,
                is_adequate=None,
                status="UNRESOLVED",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            )

        # Fully resolved: available promoter contribution is known (could be 0.0)
        req_amount = round(total_project_cost * (scheme_margin_percentage / 100.0), 2)
        actual_pct = round((available_promoter_contribution / total_project_cost) * 100.0, 2)
        diff = round(available_promoter_contribution - req_amount, 2)
        is_adequate = diff >= -1.0  # within 1 rupee rounding tolerance

        rc = M5ReasonCode.PROMOTER_CONTRIBUTION_ADEQUATE if is_adequate else M5ReasonCode.PROMOTER_CONTRIBUTION_GAP
        if available_promoter_contribution == 0.0:
            rc = M5ReasonCode.EXPLICIT_ZERO_PROMOTER if is_adequate else M5ReasonCode.PROMOTER_CONTRIBUTION_GAP

        prov.record(
            metric="required_promoter_contribution",
            value=req_amount,
            source="SCHEME_RULE",
            source_reference=f"Scheme margin of {scheme_margin_percentage:.1f}% on ₹{total_project_cost:,.2f}",
            calculation_method="Multiplication of project cost by scheme margin percentage"
        )
        prov.record(
            metric="promoter_gap_surplus",
            value=diff,
            source="DERIVED",
            source_reference="Available vs Required promoter contribution",
            calculation_method="available_promoter_contribution - required_promoter_contribution"
        )

        return PromoterContributionAnalysisResult(
            total_project_cost=total_project_cost,
            available_promoter_contribution=available_promoter_contribution,
            required_promoter_contribution=req_amount,
            required_percentage=scheme_margin_percentage,
            actual_percentage=actual_pct,
            gap_surplus=diff,
            is_adequate=is_adequate,
            status="RESOLVED",
            reason_code=rc
        )


promoter_contribution_analysis_engine = PromoterContributionAnalysisEngine()
