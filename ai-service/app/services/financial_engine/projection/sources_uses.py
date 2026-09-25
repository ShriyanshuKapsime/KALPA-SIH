"""
Sources and Uses Bridge for Milestone 3 Financial Projection Engine.
Provides a strict, auditable reconciliation of project funding sources and project cost uses.
Never invents a balancing figure.
"""
from typing import Optional, Dict, Any
from app.schemas.financial_analysis import (
    FundingSourcesUses,
    ProjectCostAnalysis,
    ProjectFinancing,
    CapitalStructure
)


class SourcesUsesEngine:
    """
    Constructs and validates the Sources and Uses of project funds.
    """

    @staticmethod
    def build(
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        capital_structure: Optional[CapitalStructure] = None,
        project_financing: Optional[ProjectFinancing] = None,
        total_project_cost: Optional[float] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> FundingSourcesUses:
        """
        Builds the institutional Sources and Uses schedule.
        """
        # Uses
        capex: Optional[float] = None
        opening_inv: Optional[float] = None
        wc_buf: Optional[float] = None
        pre_op: Optional[float] = None
        contingency: Optional[float] = None

        if project_cost_analysis is not None:
            capex = project_cost_analysis.capex
            opening_inv = project_cost_analysis.opening_inventory
            wc_buf = project_cost_analysis.working_capital
            pre_op = project_cost_analysis.pre_operating_cost
            contingency = project_cost_analysis.contingency
            if getattr(project_cost_analysis, "status", None) == "RESOLVED":
                if pre_op is None:
                    pre_op = 0.0
                if contingency is None:
                    contingency = 0.0
                if wc_buf is None:
                    wc_buf = 0.0
        elif capital_structure is not None:
            capex = capital_structure.fixed_capital_capex
            wc_buf = capital_structure.working_capital

        if user_inputs:
            if pre_op is None and user_inputs.get("pre_operating_cost") is not None:
                pre_op = float(user_inputs["pre_operating_cost"])
            if contingency is None and user_inputs.get("contingency") is not None:
                contingency = float(user_inputs["contingency"])
            if capex is None and user_inputs.get("capex") is not None:
                capex = float(user_inputs["capex"])
            elif capex is None and user_inputs.get("capex_override") is not None:
                capex = float(user_inputs["capex_override"])
            if opening_inv is None and user_inputs.get("opening_inventory") is not None:
                opening_inv = float(user_inputs["opening_inventory"])
            if wc_buf is None and user_inputs.get("working_capital_buffer") is not None:
                wc_buf = float(user_inputs["working_capital_buffer"])

        # Calculate Total Uses:
        # total_uses may be calculated only when all required components are resolved OR an authoritative aggregate exists
        auth_total: Optional[float] = None
        if total_project_cost is not None and isinstance(total_project_cost, (int, float)) and total_project_cost > 0:
            auth_total = float(total_project_cost)
        elif project_cost_analysis is not None and project_cost_analysis.total_project_cost is not None and project_cost_analysis.total_project_cost > 0:
            auth_total = float(project_cost_analysis.total_project_cost)
        elif capital_structure is not None and capital_structure.total_project_cost is not None and capital_structure.total_project_cost > 0:
            auth_total = float(capital_structure.total_project_cost)
        elif user_inputs:
            for k in ("preferred_project_cost", "total_project_cost", "project_cost"):
                if user_inputs.get(k) is not None:
                    try:
                        v = float(user_inputs[k])
                        if v > 0:
                            auth_total = v
                            break
                    except (ValueError, TypeError):
                        pass

        req_components = [capex, opening_inv, wc_buf, pre_op, contingency]
        all_resolved = all(v is not None for v in req_components)
        any_resolved = any(v is not None for v in req_components)

        total_uses: Optional[float] = None
        allocation_status = "FULLY_ALLOCATED"

        if all_resolved:
            total_uses = round(sum(req_components), 2)
            allocation_status = "FULLY_ALLOCATED"
        elif auth_total is not None:
            total_uses = round(auth_total, 2)
            allocation_status = "PARTIALLY_ALLOCATED" if any_resolved else "AGGREGATE_ONLY"
        else:
            total_uses = None
            allocation_status = "INSUFFICIENT_DATA"

        # Sources
        promoter_contrib: Optional[float] = None
        term_loan: Optional[float] = None
        other_fin: Optional[float] = None

        if capital_structure is not None:
            promoter_contrib = capital_structure.margin_contribution
            term_loan = capital_structure.loan_component
        elif project_financing is not None:
            promoter_contrib = project_financing.required_margin
            term_loan = project_financing.estimated_financeable_loan
        elif project_cost_analysis is not None:
            promoter_contrib = project_cost_analysis.promoter_margin
            debt_val = project_cost_analysis.debt_component
            term_loan = debt_val

        source_items = [v for v in (promoter_contrib, term_loan) if v is not None]
        if other_fin is not None:
            source_items.append(other_fin)
        total_sources: Optional[float] = round(sum(source_items), 2) if source_items else None

        diff: Optional[float] = None
        is_reconciled = False
        if total_sources is not None and total_uses is not None:
            diff = round(total_sources - total_uses, 2)
            is_reconciled = abs(diff) <= 1.0

        if total_sources is None or total_uses is None:
            status = "INSUFFICIENT_DATA"
            notes = "Insufficient data to reconcile sources and uses."
        elif is_reconciled:
            status = "RECONCILED"
            if allocation_status == "AGGREGATE_ONLY":
                notes = f"Sources ({total_sources:,.2f}) balance Uses ({total_uses:,.2f}) at aggregate level only; component breakdown is unallocated."
            elif allocation_status == "PARTIALLY_ALLOCATED":
                notes = f"Sources ({total_sources:,.2f}) balance Uses ({total_uses:,.2f}) with partial component allocation."
            else:
                notes = f"Sources ({total_sources:,.2f}) perfectly balance Uses ({total_uses:,.2f})."
        else:
            status = "MISMATCH"
            notes = f"Funding mismatch detected: Total Sources {total_sources:,.2f} vs Total Uses {total_uses:,.2f} (diff: {diff:,.2f})."

        return FundingSourcesUses(
            status=status,
            capex=capex,
            opening_inventory=opening_inv,
            working_capital_buffer=wc_buf,
            pre_operating_cost=pre_op,
            contingency=contingency,
            total_uses=total_uses,
            promoter_contribution=promoter_contrib,
            term_loan=term_loan,
            other_financing=other_fin,
            total_sources=total_sources,
            difference=diff,
            allocation_status=allocation_status,
            notes=notes
        )


sources_uses_engine = SourcesUsesEngine()
