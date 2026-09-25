"""
Deterministic Scenario & Sensitivity Engine for Milestone 3.
Provides Base, Upside, and Downside projections without inventing arbitrary percentages.
Only generates scenarios when explicit adjustment parameters are supplied.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import ProjectionScenario


class SensitivityEngine:
    """
    Evaluates scenario adjustments deterministically.
    """

    @staticmethod
    def evaluate_scenarios(
        base_annual_revenue: Optional[float],
        base_annual_cogs: Optional[float],
        base_annual_opex: Optional[float],
        scenario_inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds scenario results based strictly on supplied parameters.
        """
        base_ebitda: Optional[float] = None
        if base_annual_revenue is not None and base_annual_cogs is not None and base_annual_opex is not None:
            base_ebitda = round(base_annual_revenue - base_annual_cogs - base_annual_opex, 2)

        scenarios: Dict[str, Any] = {
            "BASE": {
                "revenue": base_annual_revenue,
                "cogs": base_annual_cogs,
                "operating_expenses": base_annual_opex,
                "ebitda": base_ebitda,
                "status": "CALCULATED" if base_ebitda is not None else "NOT_EVALUABLE",
                "description": "Base projection model (operating-level sensitivity only).",
                "scope": "OPERATING_LEVEL_ONLY",
                "scope_note": "This sensitivity analysis covers revenue, COGS, OpEx, and EBITDA only. It does NOT propagate through P&L, cash flow, debt, balance sheet, ratios, or viability. Full financial scenario analysis is reserved for M4."
            }
        }

        if not scenario_inputs:
            return scenarios

        # Process UPSIDE if supplied
        upside_cfg = scenario_inputs.get("UPSIDE")
        if upside_cfg and isinstance(upside_cfg, dict):
            rev_adj = float(upside_cfg.get("revenue_adjustment", 0.0))
            cost_adj = float(upside_cfg.get("cost_adjustment", 0.0))

            up_rev = round(base_annual_revenue * (1.0 + rev_adj), 2) if base_annual_revenue is not None else None
            up_cogs = round(base_annual_cogs * (1.0 + cost_adj), 2) if base_annual_cogs is not None else None
            up_opex = round(base_annual_opex * (1.0 + cost_adj), 2) if base_annual_opex is not None else None
            up_ebitda: Optional[float] = None
            if up_rev is not None and up_cogs is not None and up_opex is not None:
                up_ebitda = round(up_rev - up_cogs - up_opex, 2)

            scenarios["UPSIDE"] = {
                "revenue": up_rev,
                "cogs": up_cogs,
                "operating_expenses": up_opex,
                "ebitda": up_ebitda,
                "status": "CALCULATED" if up_ebitda is not None else "NOT_EVALUABLE",
                "scope": "OPERATING_LEVEL_ONLY",
                "description": upside_cfg.get("description", f"Upside scenario (+{rev_adj*100:.1f}% rev).")
            }

        # Process DOWNSIDE if supplied
        downside_cfg = scenario_inputs.get("DOWNSIDE")
        if downside_cfg and isinstance(downside_cfg, dict):
            rev_adj = float(downside_cfg.get("revenue_adjustment", 0.0))
            cost_adj = float(downside_cfg.get("cost_adjustment", 0.0))

            down_rev = round(base_annual_revenue * (1.0 + rev_adj), 2) if base_annual_revenue is not None else None
            down_cogs = round(base_annual_cogs * (1.0 + cost_adj), 2) if base_annual_cogs is not None else None
            down_opex = round(base_annual_opex * (1.0 + cost_adj), 2) if base_annual_opex is not None else None
            down_ebitda: Optional[float] = None
            if down_rev is not None and down_cogs is not None and down_opex is not None:
                down_ebitda = round(down_rev - down_cogs - down_opex, 2)

            scenarios["DOWNSIDE"] = {
                "revenue": down_rev,
                "cogs": down_cogs,
                "operating_expenses": down_opex,
                "ebitda": down_ebitda,
                "status": "CALCULATED" if down_ebitda is not None else "NOT_EVALUABLE",
                "scope": "OPERATING_LEVEL_ONLY",
                "description": downside_cfg.get("description", f"Downside scenario ({rev_adj*100:.1f}% rev).")
            }

        return scenarios


sensitivity_engine = SensitivityEngine()
