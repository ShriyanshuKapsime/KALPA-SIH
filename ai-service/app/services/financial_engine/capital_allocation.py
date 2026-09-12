"""
Capital Allocation Engine for Stage 9 Financial Engine.
Calculates deterministic CapEx (Fixed Capital) and Working Capital splits.
Validates that CapEx + Working Capital strictly equal 100% of the project cost.
"""
from typing import Optional, Tuple
from app.schemas.financial_analysis import CapitalStructure, ProjectFinancing
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData
from app.services.financial_engine.constants import DEFAULT_CAPITAL_ALLOCATION


class CapitalAllocationEngine:
    """
    Allocates total project cost into Fixed Capital (CapEx) and Working Capital.
    """

    @staticmethod
    def allocate_capital(
        total_project_cost: float,
        project_financing: ProjectFinancing,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        capex_override: Optional[float] = None,
        working_capital_override: Optional[float] = None
    ) -> CapitalStructure:
        """
        Determines CapEx and Working Capital components with provenance tracking.
        """
        cost = max(0.0, float(total_project_cost))

        if cost == 0.0:
            return CapitalStructure(
                total_project_cost=0.0,
                fixed_capital_capex=0.0,
                working_capital=0.0,
                capex_percentage=70.0,
                working_capital_percentage=30.0,
                margin_contribution=0.0,
                loan_component=0.0,
                source="CALCULATED"
            )

        # 1. User overrides have highest priority
        if capex_override is not None and working_capital_override is not None:
            c_over = float(capex_override)
            w_over = float(working_capital_override)
            total_alloc = c_over + w_over
            if total_alloc > 0:
                capex_pct = round((c_over / total_alloc) * 100.0, 1)
                wc_pct = round(100.0 - capex_pct, 1)
                capex_amt = round(cost * (capex_pct / 100.0), 2)
                wc_amt = round(cost - capex_amt, 2)
                source = "USER_INPUT"
            else:
                capex_pct = DEFAULT_CAPITAL_ALLOCATION["capex_percentage"]
                wc_pct = DEFAULT_CAPITAL_ALLOCATION["working_capital_percentage"]
                capex_amt = round(cost * (capex_pct / 100.0), 2)
                wc_amt = round(cost - capex_amt, 2)
                source = "CALCULATED_DEFAULT"
        elif benchmark_data:
            # 2. Benchmark data
            capex_pct = float(benchmark_data.capex_percentage)
            wc_pct = float(benchmark_data.working_capital_percentage)
            
            # Validate 100% sum
            if abs((capex_pct + wc_pct) - 100.0) > 0.01:
                total_pct = capex_pct + wc_pct
                capex_pct = round((capex_pct / total_pct) * 100.0, 1)
                wc_pct = round(100.0 - capex_pct, 1)

            capex_amt = round(cost * (capex_pct / 100.0), 2)
            wc_amt = round(cost - capex_amt, 2)
            source = "BENCHMARK_DATABASE"
        else:
            # 3. Standard MSME default
            capex_pct = DEFAULT_CAPITAL_ALLOCATION["capex_percentage"]
            wc_pct = DEFAULT_CAPITAL_ALLOCATION["working_capital_percentage"]
            capex_amt = round(cost * (capex_pct / 100.0), 2)
            wc_amt = round(cost - capex_amt, 2)
            source = "CALCULATED_DEFAULT"

        margin_contrib = min(project_financing.required_margin, cost)
        loan_comp = max(0.0, round(cost - margin_contrib, 2))

        return CapitalStructure(
            total_project_cost=cost,
            fixed_capital_capex=capex_amt,
            working_capital=wc_amt,
            capex_percentage=capex_pct,
            working_capital_percentage=wc_pct,
            margin_contribution=margin_contrib,
            loan_component=loan_comp,
            source=source
        )


# Global singleton instance
capital_allocation_engine = CapitalAllocationEngine()
