"""
Milestone 2: Deterministic Project Cost Reconciliation Engine.
Reconciles bottom-up calculated project cost against scheme financeable limits
and user-requested project cost.
Never confuses PROJECT COST with FINANCEABLE PROJECT COST.
Never replaces unknown scheme financeable project cost with calculated project cost.
Zero LLM calculations.
"""
import logging
from typing import Optional
from app.schemas.financial_analysis import ProjectCostReconciliation

logger = logging.getLogger(__name__)


class ProjectCostReconciler:
    """
    Deterministic reconciler for project cost vs scheme financeable capacity.
    """

    def reconcile(
        self,
        calculated_project_cost: Optional[float],
        scheme_financeable_project_cost: Optional[float],
        user_requested_project_cost: Optional[float] = None,
        promoter_margin: Optional[float] = None,
        debt_component: Optional[float] = None,
        is_partially_derived: bool = False,
    ) -> ProjectCostReconciliation:
        """
        Reconciles calculated project cost with scheme financeable bounds and user requests.
        Keeps all 5 financial dimensions strictly distinct:
        - calculated_project_cost
        - scheme_financeable_project_cost
        - user_requested_project_cost
        - promoter_margin
        - debt_component
        """
        if calculated_project_cost is None or calculated_project_cost <= 0:
            return ProjectCostReconciliation(
                calculated_project_cost=None,
                scheme_financeable_project_cost=scheme_financeable_project_cost,
                user_requested_project_cost=user_requested_project_cost,
                variance=None,
                reconciliation_status="INSUFFICIENT_DATA",
                reconciliation_explanation="Cannot reconcile project cost: bottom-up calculation yielded insufficient data.",
                promoter_margin=promoter_margin,
                debt_component=debt_component,
                unexplained_amount=0.0
            )

        calc_cost = round(calculated_project_cost, 2)
        user_cost = round(user_requested_project_cost, 2) if user_requested_project_cost and user_requested_project_cost > 0 else None

        # Compute unexplained amount if user requested a higher budget than bottom-up sum
        unexplained = 0.0
        if user_cost and user_cost > calc_cost:
            unexplained = round(user_cost - calc_cost, 2)

        # Handle unknown scheme financeable project cost: NEVER replace with calc_cost!
        if scheme_financeable_project_cost is None or scheme_financeable_project_cost <= 0:
            status = "PARTIALLY_DERIVED" if is_partially_derived else "INSUFFICIENT_DATA"
            explanation = (
                f"Bottom-up calculated project cost is ₹{calc_cost:,.2f}. "
                f"Scheme financeable project cost limit is unknown or unconstrained by current scheme rules."
            )
            if unexplained > 0:
                explanation += f" Entrepreneur requested ₹{user_cost:,.2f}, leaving ₹{unexplained:,.2f} unallocated."

            return ProjectCostReconciliation(
                calculated_project_cost=calc_cost,
                scheme_financeable_project_cost=None,
                user_requested_project_cost=user_cost,
                variance=None,
                reconciliation_status=status,
                reconciliation_explanation=explanation,
                promoter_margin=promoter_margin,
                debt_component=debt_component,
                unexplained_amount=unexplained
            )

        scheme_cost = round(scheme_financeable_project_cost, 2)
        # Variance = calculated project cost - scheme financeable capacity
        variance = round(calc_cost - scheme_cost, 2)

        if variance > 100.0:
            status = "FINANCING_CONSTRAINED"
            explanation = (
                f"Project economic cost (₹{calc_cost:,.2f}) exceeds the maximum scheme financeable capacity "
                f"(₹{scheme_cost:,.2f}) by ₹{variance:,.2f}. The project requires additional promoter equity or "
                f"supplementary financing to bridge the ₹{variance:,.2f} gap."
            )
        elif is_partially_derived:
            status = "PARTIALLY_DERIVED"
            explanation = (
                f"Calculated project cost of ₹{calc_cost:,.2f} is within scheme capacity (₹{scheme_cost:,.2f}). "
                f"Certain components are derived from benchmarks rather than verified bills/quotes."
            )
        else:
            status = "FULLY_RECONCILED"
            explanation = (
                f"Bottom-up calculated project cost of ₹{calc_cost:,.2f} is fully reconciled with "
                f"scheme financeable capacity (₹{scheme_cost:,.2f})."
            )

        if unexplained > 0:
            explanation += f" Note: Entrepreneur requested ₹{user_cost:,.2f}, leaving ₹{unexplained:,.2f} currently unallocated to specific CapEx/OpEx components."

        return ProjectCostReconciliation(
            calculated_project_cost=calc_cost,
            scheme_financeable_project_cost=scheme_cost,
            user_requested_project_cost=user_cost,
            variance=variance,
            reconciliation_status=status,
            reconciliation_explanation=explanation,
            promoter_margin=promoter_margin,
            debt_component=debt_component,
            unexplained_amount=unexplained
        )


# Global singleton
project_cost_reconciler = ProjectCostReconciler()
