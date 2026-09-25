"""
Financing Structure Engine for M4 Banking Appraisal.
Produces DPR-ready sources and uses reconciliation, identifying financing surplus/gap,
debt/equity mix, and unresolved components.
"""
from typing import Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    FinancingStructureResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    FundingSourcesUses,
    ProjectCostAnalysis,
    CapitalStructure,
    ProjectFinancing
)


class FinancingStructureEngine:
    """
    Deterministic financing structure appraisal engine.
    """

    def evaluate(
        self,
        sources_uses: Optional[FundingSourcesUses] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        capital_structure: Optional[CapitalStructure] = None,
        project_financing: Optional[ProjectFinancing] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> FinancingStructureResult:
        prov = provenance or ProvenanceBuilder()

        # Extract Uses (Project Cost components)
        total_uses: Optional[float] = None
        if sources_uses and sources_uses.total_uses is not None and sources_uses.total_uses > 0:
            total_uses = sources_uses.total_uses
        elif project_cost_analysis and project_cost_analysis.total_project_cost is not None and project_cost_analysis.total_project_cost > 0:
            total_uses = project_cost_analysis.total_project_cost
        elif capital_structure and capital_structure.total_project_cost > 0:
            total_uses = capital_structure.total_project_cost

        # Extract Sources (Equity, Term Loan, WC Loan, Other)
        promoter_contrib: Optional[float] = None
        term_loan: Optional[float] = None
        wc_fin: Optional[float] = None
        other_fin: Optional[float] = None
        total_sources: Optional[float] = None

        if sources_uses:
            promoter_contrib = sources_uses.promoter_contribution
            term_loan = sources_uses.term_loan
            other_fin = sources_uses.other_financing
            total_sources = sources_uses.total_sources

        if promoter_contrib is None and project_financing:
            promoter_contrib = project_financing.available_margin
        if term_loan is None and project_financing:
            term_loan = project_financing.estimated_financeable_loan

        if total_sources is None:
            if promoter_contrib is not None and term_loan is not None:
                add_other = other_fin if other_fin is not None else 0.0
                add_wc = wc_fin if wc_fin is not None else 0.0
                total_sources = round(promoter_contrib + term_loan + add_other + add_wc, 2)

        # Check for unresolved components
        unresolved_comp = None
        if total_uses is None:
            unresolved_comp = "total_project_cost"
        elif promoter_contrib is None:
            unresolved_comp = "promoter_contribution"
        elif term_loan is None:
            unresolved_comp = "term_loan"

        if unresolved_comp is not None or total_uses is None or total_sources is None:
            return FinancingStructureResult(
                status=AppraisalStatus.UNRESOLVED,
                total_project_cost=total_uses,
                promoter_contribution=promoter_contrib,
                term_loan=term_loan,
                working_capital_financing=wc_fin,
                other_financing=other_fin,
                total_sources=total_sources,
                total_uses=total_uses,
                financing_gap_surplus=None,
                debt_equity_mix=None,
                is_balanced=False,
                unresolved_component=unresolved_comp,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        gap_surplus = round(total_sources - total_uses, 2)
        is_balanced = abs(gap_surplus) <= 1.0  # 1 INR rounding tolerance

        # Debt / Equity mix
        debt_part = term_loan + (wc_fin if wc_fin is not None else 0.0)
        equity_part = promoter_contrib + (other_fin if other_fin is not None else 0.0)
        tot_cap = debt_part + equity_part
        if tot_cap > 0:
            d_pct = round((debt_part / tot_cap) * 100.0)
            e_pct = round((equity_part / tot_cap) * 100.0)
            mix_str = f"{e_pct}:{d_pct}"
        else:
            mix_str = None

        rc = ReasonCode.FINANCING_GAP if gap_surplus < -1.0 else (
            ReasonCode.FINANCING_SURPLUS if gap_surplus > 1.0 else None
        )

        prov.record(
            metric="financing_sources_vs_uses",
            value=gap_surplus,
            source=MetricSource.DERIVED,
            source_reference="Funding Sources and Uses Reconciliation",
            calculation_method="Total Sources - Total Uses",
            status=AppraisalStatus.RESOLVED,
            dependencies=["sources_uses", "project_cost_analysis"]
        )

        return FinancingStructureResult(
            status=AppraisalStatus.RESOLVED,
            total_project_cost=total_uses,
            promoter_contribution=promoter_contrib,
            term_loan=term_loan,
            working_capital_financing=wc_fin,
            other_financing=other_fin,
            total_sources=total_sources,
            total_uses=total_uses,
            financing_gap_surplus=gap_surplus,
            debt_equity_mix=mix_str,
            is_balanced=is_balanced,
            unresolved_component=None,
            reason_code=rc
        )


financing_structure_engine = FinancingStructureEngine()
