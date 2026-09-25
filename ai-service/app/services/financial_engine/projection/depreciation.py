"""
Deterministic Depreciation Engine for Milestone 3.
Implements Straight Line Method (SLM) depreciation.
Generates annual depreciation, accumulated depreciation, and net block per year.
Preserves non-depreciable assets like land.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    ProjectCostAnalysis,
    CapitalStructure,
    DepreciationScheduleYear,
)


class DepreciationEngine:
    """
    Deterministic Straight Line Method (SLM) depreciation calculation.
    """

    @staticmethod
    def calculate_schedule(
        projection_years: int = 5,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        capital_structure: Optional[CapitalStructure] = None,
        useful_life_years: Optional[float] = None,
        salvage_value: float = 0.0,
        user_inputs: Optional[Dict[str, Any]] = None,
        benchmark_data: Optional[Any] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
    ) -> Dict[int, DepreciationScheduleYear]:
        """
        Builds Year 1..N depreciation schedule.
        """
        user_in = user_inputs or {}
        asm_map = assumptions_map or {}

        # 1. Determine Depreciable Asset Cost (CapEx excluding land)
        capex: Optional[float] = None
        land_cost: float = 0.0

        if project_cost_analysis is not None and project_cost_analysis.capex is not None:
            capex = float(project_cost_analysis.capex)
            # Check if land is separated in capex decomposition
            cd = project_cost_analysis.capex_decomposition
            if cd is not None and hasattr(cd, "components") and getattr(cd, "components", None):
                for comp in cd.components:
                    cat = getattr(comp, "category", "") or ""
                    title = getattr(comp, "title", "") or ""
                    if "land" in cat.lower() or "land" in title.lower():
                        land_cost += float(getattr(comp, "amount", 0.0) or 0.0)
        elif capital_structure is not None and capital_structure.fixed_capital_capex is not None:
            capex = float(capital_structure.fixed_capital_capex)
        elif user_in.get("capex_override") is not None:
            try:
                capex = float(user_in["capex_override"])
            except (ValueError, TypeError):
                pass
        elif user_in.get("capex") is not None:
            try:
                capex = float(user_in["capex"])
            except (ValueError, TypeError):
                pass

        if user_in.get("land_cost") is not None:
            try:
                land_cost += float(user_in["land_cost"])
            except (ValueError, TypeError):
                pass

        # Zero CapEx explicitly -> immediately return RESOLVED zero depreciation schedule.
        # Useful life is NOT required for zero-CapEx businesses.
        if capex == 0.0:
            zero_sched: Dict[int, DepreciationScheduleYear] = {}
            for y in range(1, projection_years + 1):
                zero_sched[y] = DepreciationScheduleYear(
                    year=y,
                    gross_block=0.0,
                    depreciation_amount=0.0,
                    accumulated_depreciation=0.0,
                    net_block=0.0,
                    status="RESOLVED",
                    notes="Zero CapEx business; no depreciable fixed assets."
                )
            return zero_sched

        # Useful life resolution: User input > benchmark data > assumptions map > None
        life = useful_life_years
        if life is None:
            for k in ("depreciation_life_years", "asset_useful_life", "useful_life"):
                if k in user_in and user_in[k] is not None:
                    try:
                        life = float(user_in[k])
                        break
                    except (ValueError, TypeError):
                        pass
        if life is None and benchmark_data:
            for attr in ("depreciation_life_years", "asset_useful_life", "useful_life_years", "depreciation_useful_life"):
                raw_val = benchmark_data.get(attr) if isinstance(benchmark_data, dict) else getattr(benchmark_data, attr, None)
                if raw_val is not None:
                    try:
                        life = float(raw_val)
                        break
                    except (ValueError, TypeError):
                        pass
            if life is None:
                rate_val = (
                    (benchmark_data.get("depreciation_rate_slm") or benchmark_data.get("depreciation_rate"))
                    if isinstance(benchmark_data, dict)
                    else (getattr(benchmark_data, "depreciation_rate_slm", None) or getattr(benchmark_data, "depreciation_rate", None))
                )
                if rate_val is not None:
                    try:
                        rate = float(rate_val)
                        if rate > 0:
                            life = round(100.0 / rate, 1) if rate > 1.0 else round(1.0 / rate, 1)
                    except (ValueError, TypeError):
                        pass
        if life is None and asm_map:
            for k in ("depreciation_life_years", "asset_useful_life", "useful_life", "depreciation_useful_life"):
                if k in asm_map and asm_map[k] is not None:
                    raw = getattr(asm_map[k], "value", asm_map[k])
                    if raw is not None:
                        try:
                            life = float(raw)
                            break
                        except (ValueError, TypeError):
                            pass
            if life is None and "depreciation_rate" in asm_map and asm_map["depreciation_rate"] is not None:
                raw = getattr(asm_map["depreciation_rate"], "value", asm_map["depreciation_rate"])
                if raw is not None:
                    try:
                        rate = float(raw)
                        if rate > 0:
                            life = round(100.0 / rate, 1) if rate > 1.0 else round(1.0 / rate, 1)
                    except (ValueError, TypeError):
                        pass

        schedule: Dict[int, DepreciationScheduleYear] = {}

        # If useful life is unresolved or invalid, do NOT assume 10 years
        if life is None or life <= 0:
            for y in range(1, projection_years + 1):
                schedule[y] = DepreciationScheduleYear(
                    year=y,
                    gross_block=capex,
                    depreciation_amount=None,
                    accumulated_depreciation=None,
                    net_block=None,
                    status="UNKNOWN",
                    notes="Useful life of fixed assets is unresolved; depreciation not modeled."
                )
            return schedule

        if capex is None:
            for y in range(1, projection_years + 1):
                schedule[y] = DepreciationScheduleYear(
                    year=y,
                    gross_block=None,
                    depreciation_amount=None,
                    accumulated_depreciation=None,
                    net_block=None,
                    status="UNKNOWN",
                    notes="CapEx is unresolved; depreciation cannot be calculated."
                )
            return schedule

        depreciable_base = max(0.0, capex - land_cost - salvage_value)
        annual_depr = round(depreciable_base / life, 2) if (life > 0 and depreciable_base > 0) else 0.0

        accum_depr = 0.0
        for y in range(1, projection_years + 1):
            accum_depr = round(accum_depr + annual_depr, 2)
            # Ensure accumulated depreciation never exceeds depreciable base
            if accum_depr > depreciable_base:
                actual_depr = max(0.0, round(depreciable_base - (accum_depr - annual_depr), 2))
                accum_depr = depreciable_base
            else:
                actual_depr = annual_depr

            net_block = round(max(0.0, capex - accum_depr), 2)

            schedule[y] = DepreciationScheduleYear(
                year=y,
                gross_block=capex,
                depreciation_amount=actual_depr,
                accumulated_depreciation=accum_depr,
                net_block=net_block,
                status="RESOLVED",
                notes=f"SLM depreciation over {life:.1f} years."
            )

        return schedule


depreciation_engine = DepreciationEngine()
