"""
Promoter Contribution Analysis Engine for M4 Banking Appraisal.
Evaluates required vs actual promoter contribution, margin compliance,
contribution percentage, and financing surplus/gap deterministically.
Strict rule: Does not alter financing structure merely to force compliance.
"""
from typing import Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    PromoterContributionResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    ProjectFinancing,
    CapitalStructure,
    FundingSourcesUses,
    ProjectCostAnalysis
)


class PromoterContributionEngine:
    """
    Deterministic promoter contribution appraisal engine.
    """

    def evaluate(
        self,
        project_financing: Optional[ProjectFinancing] = None,
        capital_structure: Optional[CapitalStructure] = None,
        sources_uses: Optional[FundingSourcesUses] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        scheme_margin_ratio: Optional[float] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> PromoterContributionResult:
        prov = provenance or ProvenanceBuilder()

        # Determine Total Project Cost
        total_cost: Optional[float] = None
        if sources_uses and sources_uses.total_uses is not None and sources_uses.total_uses > 0:
            total_cost = sources_uses.total_uses
        elif project_cost_analysis and project_cost_analysis.total_project_cost is not None and project_cost_analysis.total_project_cost > 0:
            total_cost = project_cost_analysis.total_project_cost
        elif capital_structure and capital_structure.total_project_cost > 0:
            total_cost = capital_structure.total_project_cost
        elif project_financing and project_financing.maximum_financeable_project_cost > 0:
            total_cost = project_financing.maximum_financeable_project_cost

        if total_cost is None or total_cost <= 0:
            return PromoterContributionResult(
                status=AppraisalStatus.UNRESOLVED,
                total_project_cost=None,
                required_promoter_contribution=None,
                actual_promoter_contribution=None,
                contribution_percentage=None,
                required_percentage=None,
                gap_surplus=None,
                is_adequate=False,
                equity_debt_mix=None,
                reason_code=ReasonCode.MISSING_PROJECT_COST
            )

        # Required Promoter Contribution
        req_margin: Optional[float] = None
        if project_financing and project_financing.required_margin is not None:
            req_margin = project_financing.required_margin
        elif scheme_margin_ratio is not None:
            req_margin = round(total_cost * scheme_margin_ratio, 2)

        # If no authoritative required margin is available, required contribution remains unresolved
        if req_margin is None:
            return PromoterContributionResult(
                status=AppraisalStatus.UNRESOLVED,
                total_project_cost=total_cost,
                required_promoter_contribution=None,
                actual_promoter_contribution=None,
                contribution_percentage=None,
                required_percentage=None,
                gap_surplus=None,
                is_adequate=False,
                equity_debt_mix=None,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        # Actual Promoter Contribution
        actual_margin: Optional[float] = None
        if sources_uses and sources_uses.promoter_contribution is not None:
            actual_margin = sources_uses.promoter_contribution
        elif project_financing and project_financing.available_margin is not None:
            actual_margin = project_financing.available_margin
        elif capital_structure and capital_structure.promoter_equity is not None:
            actual_margin = capital_structure.promoter_equity

        if actual_margin is None:
            return PromoterContributionResult(
                status=AppraisalStatus.UNRESOLVED,
                total_project_cost=total_cost,
                required_promoter_contribution=req_margin,
                actual_promoter_contribution=None,
                contribution_percentage=None,
                required_percentage=round((req_margin / total_cost) * 100.0, 2) if req_margin else None,
                gap_surplus=None,
                is_adequate=False,
                equity_debt_mix=None,
                reason_code=ReasonCode.MISSING_EQUITY
            )

        gap_surplus = round(actual_margin - req_margin, 2)
        contrib_pct = round((actual_margin / total_cost) * 100.0, 2)
        req_pct = round((req_margin / total_cost) * 100.0, 2)
        is_adequate = gap_surplus >= 0.0

        debt_pct = max(0.0, round(100.0 - contrib_pct, 2))
        mix_str = f"{round(contrib_pct):.0f}:{round(debt_pct):.0f}"

        prov.record(
            metric="actual_promoter_contribution",
            value=actual_margin,
            source=MetricSource.USER if (project_financing and actual_margin == project_financing.available_margin) else MetricSource.DERIVED,
            source_reference="Project Financing / Sources and Uses",
            calculation_method="Evaluated against scheme requirements",
            status=AppraisalStatus.RESOLVED,
            dependencies=["project_financing", "sources_uses"]
        )

        return PromoterContributionResult(
            status=AppraisalStatus.RESOLVED,
            total_project_cost=total_cost,
            required_promoter_contribution=req_margin,
            actual_promoter_contribution=actual_margin,
            contribution_percentage=contrib_pct,
            required_percentage=req_pct,
            gap_surplus=gap_surplus,
            is_adequate=is_adequate,
            equity_debt_mix=mix_str,
            reason_code=ReasonCode.PROMOTER_CONTRIBUTION_ADEQUATE if is_adequate else ReasonCode.PROMOTER_CONTRIBUTION_GAP
        )


promoter_contribution_engine = PromoterContributionEngine()
