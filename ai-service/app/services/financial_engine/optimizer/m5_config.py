"""
M5 Centralized Policy Configuration.
Defines explicit, deterministic policy scenario parameters, resilience thresholds,
and selection hierarchies for stress testing and financing optimization.
Zero scattered hardcoded magic numbers.
"""
from typing import Dict, Any


# -----------------------------------------------------------------------------
# Engine Versions
# -----------------------------------------------------------------------------
POLICY_VERSION: str = "1.0.0"
MODEL_VERSION: str = "M5-1.0.0"

# -----------------------------------------------------------------------------
# Deterministic Policy Scenario Stress Parameters
# (Applied when driver is available; never applied if driver is unresolved)
# -----------------------------------------------------------------------------
POLICY_STRESS_PARAMETERS: Dict[str, Dict[str, Any]] = {
    "REVENUE_DOWNSIDE": {
        "scenario_id": "STRESS_REV_DOWN_15",
        "scenario_name": "Revenue Downside (-15%)",
        "description": "Simulates a 15% reduction in top-line sales revenue due to market headwinds or delayed traction.",
        "revenue_reduction_pct": 15.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.85
    },
    "SELLING_PRICE_DOWNSIDE": {
        "scenario_id": "STRESS_PRICE_DOWN_10",
        "scenario_name": "Selling Price Realization Downside (-10%)",
        "description": "Simulates a 10% price realization discount while maintaining unit volume.",
        "price_reduction_pct": 10.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.85
    },
    "VOLUME_DOWNSIDE": {
        "scenario_id": "STRESS_VOL_DOWN_10",
        "scenario_name": "Sales Volume / Capacity Utilization Downside (-10%)",
        "description": "Simulates a 10% drop in unit volume/utilization with proportional reduction in variable costs.",
        "volume_reduction_pct": 10.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.85
    },
    "VARIABLE_COST_INCREASE": {
        "scenario_id": "STRESS_VAR_COST_UP_10",
        "scenario_name": "Raw Material / COGS Input Inflation (+10%)",
        "description": "Simulates a 10% increase in COGS/variable operating costs due to supply chain inflation.",
        "variable_cost_increase_pct": 10.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.85
    },
    "FIXED_COST_INCREASE": {
        "scenario_id": "STRESS_FIX_COST_UP_10",
        "scenario_name": "Fixed Overhead Cost Creep (+10%)",
        "description": "Simulates a 10% escalation in fixed operating overheads (rent, compliance, admin).",
        "fixed_cost_increase_pct": 10.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.85
    },
    "WORKING_CAPITAL_PRESSURE": {
        "scenario_id": "STRESS_WC_PRESSURE_15",
        "scenario_name": "Working Capital Cycle Elongation (+15%)",
        "description": "Simulates a 15% increase in working capital requirement due to extended customer receivables or buffer inventory.",
        "wc_increase_pct": 15.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.80
    },
    "INTEREST_RATE_STRESS": {
        "scenario_id": "STRESS_RATE_HIKE_150BPS",
        "scenario_name": "Interest Rate Shock (+1.50% / 150 bps)",
        "description": "Simulates a 150 bps increase in borrowing costs where floating rate terms or refinancing apply.",
        "rate_increase_pct_points": 1.50,
        "source": "POLICY_SCENARIO",
        "confidence": 0.90
    },
    "COMBINED_DOWNSIDE": {
        "scenario_id": "STRESS_COMBINED_DOWNSIDE",
        "scenario_name": "Severe Combined Stress (Revenue -10%, Costs +5%, WC +10%)",
        "description": "Simultaneous macro stress combining moderate revenue decline, cost inflation, and working capital tightening.",
        "revenue_reduction_pct": 10.0,
        "variable_cost_increase_pct": 5.0,
        "fixed_cost_increase_pct": 5.0,
        "wc_increase_pct": 10.0,
        "source": "POLICY_SCENARIO",
        "confidence": 0.80
    }
}

# -----------------------------------------------------------------------------
# Transparent Resilience Thresholds (POLICY_THRESHOLD)
# -----------------------------------------------------------------------------
DSCR_RESILIENCE_BENCHMARK: float = 1.25     # Normal institutional benchmark
DSCR_RESILIENCE_MINIMUM: float = 1.10       # Minimum acceptable under downside stress
CURRENT_RATIO_RESILIENCE_MINIMUM: float = 1.10
CASH_BUFFER_RESILIENCE_MONTHS: float = 1.0  # Minimum 1 month operating expenses
BREAK_EVEN_MAX_UTILIZATION: float = 85.0    # Above 85% is critical vulnerability
MAX_ACCEPTABLE_DER: float = 4.0             # DER ceiling under policy

# -----------------------------------------------------------------------------
# Transparent Severity & Worst-Case Scenario Selection Hierarchy
# -----------------------------------------------------------------------------
# 1. Macro Severity Tier:
#    CRITICAL > STRESSED > RESILIENT > NOT_ASSESSABLE / UNRESOLVED
# 2. Within the same severity tier, scenarios are ranked using deterministic policy ordering:
#    a. Financing Gap Shortfall (descending: highest gap first)
#    b. DSCR (ascending: lowest DSCR first)
#    c. Liquidity / Current Ratio (ascending: lowest ratio first)
#    d. Cash Buffer Months (ascending: shortest buffer first)
#    e. Break-Even Utilization % (descending: highest utilization first)
# -----------------------------------------------------------------------------
SEVERITY_ORDER: Dict[str, int] = {
    "CRITICAL": 1,
    "STRESSED": 2,
    "RESILIENT": 3,
    "NOT_ASSESSABLE": 4,
    "UNRESOLVED": 5
}

