"""
Break-Even Engine for Stage 9 Financial Engine.
Calculates deterministic Contribution Margin, Contribution Margin Ratio,
Monthly and Annual Break-Even Revenue, Break-Even Units, and Capacity Utilization.
Emits INSUFFICIENT_DATA status if required cost/revenue parameters are missing.
"""
from typing import Optional
from app.schemas.financial_analysis import (
    BreakEvenAnalysis,
    CalculationStatus,
    ProfitabilityProjection,
    ProjectAssumptionsInput
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


class BreakEvenEngine:
    """
    Deterministic break-even analysis engine.
    """

    @staticmethod
    def calculate_break_even(
        profitability: ProfitabilityProjection,
        project_assumptions: ProjectAssumptionsInput,
        benchmark_data: Optional[BenchmarkFinancialData] = None
    ) -> BreakEvenAnalysis:
        """
        Calculates break-even financial metrics and operational capacity utilization.
        """
        if (
            profitability.status != CalculationStatus.CALCULATED or
            profitability.monthly_revenue is None or
            profitability.monthly_revenue <= 0
        ):
            return BreakEvenAnalysis(
                status=CalculationStatus.INSUFFICIENT_DATA,
                notes="Break-even calculation requires verified revenue and cost structure."
            )

        revenue = float(profitability.monthly_revenue)
        cogs = float(profitability.monthly_cogs or 0.0)
        opex = float(profitability.monthly_operating_expenses or 0.0)

        # 1. Split Fixed vs Variable Costs
        if benchmark_data and benchmark_data.fixed_cost_ratio:
            fixed_ratio = float(benchmark_data.fixed_cost_ratio)
        else:
            fixed_ratio = 0.35  # Standard MSME operational fixed cost assumption (rent, base staff, licenses)

        fixed_ratio = max(0.10, min(0.80, fixed_ratio))
        var_ratio = 1.0 - fixed_ratio

        # Variable costs = COGS + variable OpEx
        variable_costs = round(cogs + (opex * var_ratio), 2)
        fixed_monthly_costs = round(opex * fixed_ratio, 2)

        # 2. Contribution Margin
        contribution_margin = round(revenue - variable_costs, 2)
        if revenue > 0:
            contribution_margin_ratio = round(contribution_margin / revenue, 4)
        else:
            contribution_margin_ratio = 0.0

        # 3. Break-Even Revenue
        if contribution_margin_ratio > 0.01:
            monthly_be_rev = round(fixed_monthly_costs / contribution_margin_ratio, 2)
            annual_be_rev = round(monthly_be_rev * 12.0, 2)
            utilization_pct = round((monthly_be_rev / revenue) * 100.0, 1)
        else:
            monthly_be_rev = None
            annual_be_rev = None
            utilization_pct = None

        # 4. Break-Even Units (if unit price / volume available)
        be_units = None
        if project_assumptions.expected_unit_price and project_assumptions.expected_unit_price > 0:
            price = float(project_assumptions.expected_unit_price)
            var_cost_per_unit = (variable_costs / float(project_assumptions.expected_monthly_units or 1.0)) if project_assumptions.expected_monthly_units else price * (1.0 - contribution_margin_ratio)
            unit_cm = price - var_cost_per_unit
            if unit_cm > 0:
                be_units = round(fixed_monthly_costs / unit_cm, 1)
        elif benchmark_data and benchmark_data.unit_economics:
            unit_econ = benchmark_data.unit_economics
            if "processing_charge_per_kg" in unit_econ:
                chg = float(unit_econ["processing_charge_per_kg"])
                if chg > 0 and monthly_be_rev:
                    be_units = round(monthly_be_rev / chg, 1)

        # 5. Months to Break-Even
        breakeven_months = benchmark_data.breakeven_months if benchmark_data else 6

        return BreakEvenAnalysis(
            status=CalculationStatus.CALCULATED,
            monthly_fixed_costs=fixed_monthly_costs,
            contribution_margin=contribution_margin,
            contribution_margin_ratio=contribution_margin_ratio,
            monthly_break_even_revenue=monthly_be_rev,
            annual_break_even_revenue=annual_be_rev,
            break_even_utilization_pct=utilization_pct,
            break_even_units=be_units,
            months_to_break_even=breakeven_months,
            notes=f"Break-even achieved at {utilization_pct}% of projected operational capacity." if utilization_pct else "Break-even computed deterministically."
        )


# Global singleton instance
break_even_engine = BreakEvenEngine()
