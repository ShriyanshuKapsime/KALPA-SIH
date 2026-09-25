"""
Scenario Definitions and Generator for M5 Downside Stress Testing.
Builds standardized deterministic scenario specifications from centralized policy
or explicit user inputs. Never fabricates numbers.
"""
from typing import Dict, Any, List, Optional
from app.services.financial_engine.optimizer.m5_config import POLICY_STRESS_PARAMETERS
from app.services.financial_engine.optimizer.m5_schema import (
    StressScenarioType,
    ScenarioSource
)


class ScenarioSpecification:
    """Represents a structured stress test definition."""
    def __init__(
        self,
        scenario_id: str,
        scenario_name: str,
        scenario_type: StressScenarioType,
        source: ScenarioSource,
        parameters: Dict[str, Any],
        affected_drivers: List[str],
        confidence: float = 0.85
    ) -> None:
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.scenario_type = scenario_type
        self.source = source
        self.parameters = parameters
        self.affected_drivers = affected_drivers
        self.confidence = confidence


class StressScenarioGenerator:
    """
    Generates standardized stress test scenarios based on centralized policy
    or verified user-provided scenario parameters.
    """

    @staticmethod
    def generate_standard_scenarios(
        user_scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> List[ScenarioSpecification]:
        specs: List[ScenarioSpecification] = []

        # 1. Base Case Spec
        specs.append(ScenarioSpecification(
            scenario_id="BASE_CASE",
            scenario_name="Base Case (Projections)",
            scenario_type=StressScenarioType.BASE_CASE,
            source=ScenarioSource.BASE_CASE,
            parameters={},
            affected_drivers=[],
            confidence=1.0
        ))

        # 2. Revenue Downside (-15%)
        p_rev = POLICY_STRESS_PARAMETERS["REVENUE_DOWNSIDE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_rev["scenario_id"],
            scenario_name=p_rev["scenario_name"],
            scenario_type=StressScenarioType.REVENUE_DOWNSIDE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"revenue_change_pct": -p_rev["revenue_reduction_pct"]},
            affected_drivers=["revenue"],
            confidence=p_rev["confidence"]
        ))

        # 3. Selling Price Downside (-10%)
        p_price = POLICY_STRESS_PARAMETERS["SELLING_PRICE_DOWNSIDE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_price["scenario_id"],
            scenario_name=p_price["scenario_name"],
            scenario_type=StressScenarioType.SELLING_PRICE_DOWNSIDE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"price_change_pct": -p_price["price_reduction_pct"]},
            affected_drivers=["unit_price", "revenue"],
            confidence=p_price["confidence"]
        ))

        # 4. Volume Downside (-10%)
        p_vol = POLICY_STRESS_PARAMETERS["VOLUME_DOWNSIDE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_vol["scenario_id"],
            scenario_name=p_vol["scenario_name"],
            scenario_type=StressScenarioType.VOLUME_DOWNSIDE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"volume_change_pct": -p_vol["volume_reduction_pct"]},
            affected_drivers=["units_sold", "revenue", "cogs"],
            confidence=p_vol["confidence"]
        ))

        # 5. Variable Cost Increase (+10%)
        p_var = POLICY_STRESS_PARAMETERS["VARIABLE_COST_INCREASE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_var["scenario_id"],
            scenario_name=p_var["scenario_name"],
            scenario_type=StressScenarioType.VARIABLE_COST_INCREASE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"variable_cost_change_pct": p_var["variable_cost_increase_pct"]},
            affected_drivers=["cogs", "variable_costs"],
            confidence=p_var["confidence"]
        ))

        # 6. Fixed Cost Increase (+10%)
        p_fix = POLICY_STRESS_PARAMETERS["FIXED_COST_INCREASE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_fix["scenario_id"],
            scenario_name=p_fix["scenario_name"],
            scenario_type=StressScenarioType.FIXED_COST_INCREASE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"fixed_cost_change_pct": p_fix["fixed_cost_increase_pct"]},
            affected_drivers=["operating_expenses", "fixed_costs"],
            confidence=p_fix["confidence"]
        ))

        # 7. Working Capital Pressure (+15%)
        p_wc = POLICY_STRESS_PARAMETERS["WORKING_CAPITAL_PRESSURE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_wc["scenario_id"],
            scenario_name=p_wc["scenario_name"],
            scenario_type=StressScenarioType.WORKING_CAPITAL_PRESSURE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"wc_change_pct": p_wc["wc_increase_pct"]},
            affected_drivers=["working_capital", "current_assets"],
            confidence=p_wc["confidence"]
        ))

        # 8. Interest Rate Stress (+1.50%)
        p_rate = POLICY_STRESS_PARAMETERS["INTEREST_RATE_STRESS"]
        specs.append(ScenarioSpecification(
            scenario_id=p_rate["scenario_id"],
            scenario_name=p_rate["scenario_name"],
            scenario_type=StressScenarioType.INTEREST_RATE_STRESS,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={"rate_hike_pct_points": p_rate["rate_increase_pct_points"]},
            affected_drivers=["interest_rate", "interest_expense", "debt_service"],
            confidence=p_rate["confidence"]
        ))

        # 9. Combined Downside Scenario
        p_comb = POLICY_STRESS_PARAMETERS["COMBINED_DOWNSIDE"]
        specs.append(ScenarioSpecification(
            scenario_id=p_comb["scenario_id"],
            scenario_name=p_comb["scenario_name"],
            scenario_type=StressScenarioType.COMBINED_DOWNSIDE,
            source=ScenarioSource.POLICY_SCENARIO,
            parameters={
                "revenue_change_pct": -p_comb["revenue_reduction_pct"],
                "variable_cost_change_pct": p_comb["variable_cost_increase_pct"],
                "fixed_cost_change_pct": p_comb["fixed_cost_increase_pct"],
                "wc_change_pct": p_comb["wc_increase_pct"]
            },
            affected_drivers=["revenue", "cogs", "operating_expenses", "working_capital"],
            confidence=p_comb["confidence"]
        ))

        # 10. Optional User-Supplied Scenarios
        if user_scenarios:
            for idx, us in enumerate(user_scenarios, start=1):
                s_id = us.get("scenario_id", f"USER_SCENARIO_{idx}")
                s_name = us.get("scenario_name", f"User Custom Scenario {idx}")
                specs.append(ScenarioSpecification(
                    scenario_id=s_id,
                    scenario_name=s_name,
                    scenario_type=StressScenarioType.USER_SCENARIO,
                    source=ScenarioSource.USER_SCENARIO,
                    parameters=us.get("parameters", {}),
                    affected_drivers=us.get("affected_drivers", []),
                    confidence=1.0
                ))

        return specs


stress_scenario_generator = StressScenarioGenerator()
