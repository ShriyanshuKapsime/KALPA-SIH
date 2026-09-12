"""
Constants and Configuration Parameters for Stage 8: Opportunity Evaluation Engine.
Provides deterministic weights, classification thresholds, penalty definitions,
and explainable factor templates.
"""
from typing import Dict, Any

# -----------------------------------------------------------------------------
# Component Weights for Opportunity Synthesis (Sum MUST equal 1.0)
# -----------------------------------------------------------------------------
OPPORTUNITY_WEIGHTS: Dict[str, float] = {
    "demand": 0.25,
    "competition": 0.20,
    "infrastructure": 0.15,
    "supply": 0.15,
    "market_access": 0.10,
    "market_capacity": 0.15
}

# Strict compile-time validation that weights sum to exactly 1.0
assert abs(sum(OPPORTUNITY_WEIGHTS.values()) - 1.0) < 1e-6, "OPPORTUNITY_WEIGHTS must sum to 1.0"

# -----------------------------------------------------------------------------
# Supply Scoring Weights (Risk vs Coverage)
# -----------------------------------------------------------------------------
SUPPLY_WEIGHTS: Dict[str, float] = {
    "risk_complement": 0.60,
    "input_coverage": 0.40
}
assert abs(sum(SUPPLY_WEIGHTS.values()) - 1.0) < 1e-6, "SUPPLY_WEIGHTS must sum to 1.0"

# -----------------------------------------------------------------------------
# Deterministic Classification Thresholds
# -----------------------------------------------------------------------------
# [0.75, 1.00] -> HIGH_OPPORTUNITY
# [0.55, 0.749] -> MODERATE_OPPORTUNITY
# [0.35, 0.549] -> LIMITED_OPPORTUNITY
# [0.00, 0.349] -> LOW_OPPORTUNITY
OPPORTUNITY_LEVEL_THRESHOLDS = {
    "HIGH": 0.75,
    "MODERATE": 0.55,
    "LIMITED": 0.35
}

# Deterministic mapping for Demand Signal Score
DEMAND_SIGNAL_THRESHOLDS = {
    "HIGH": 0.70,
    "MODERATE": 0.40
}

# -----------------------------------------------------------------------------
# Critical Constraint Penalties and Rules
# -----------------------------------------------------------------------------
CONSTRAINT_PENALTIES = {
    "MARKET_SATURATION_SCORE_THRESHOLD": 0.30,
    "CRITICAL_GAP_PENALTY_PER_ITEM": 0.10,
    "EXTREME_SUPPLY_FAILURE_PENALTY": 0.15,
    "SEVERE_COMPETITION_PENALTY": 0.10,
    "DATA_CONFIDENCE_DISCOUNT_PROXY": 0.10,
    "DATA_CONFIDENCE_DISCOUNT_MISSING": 0.10
}

# -----------------------------------------------------------------------------
# Factor Templates (Deterministic Rule-Based Strings — Zero LLM)
# -----------------------------------------------------------------------------
POSITIVE_FACTOR_TEMPLATES = {
    "STRONG_DEMAND": "Strong demand evidence detected in the target market.",
    "LOW_COMPETITION": "Low competitive pressure in the relevant catchment.",
    "INFRASTRUCTURE_AVAILABLE": "Required business infrastructure is available.",
    "CAPACITY_EXPANSION": "Available market capacity supports additional business activity.",
    "HIGH_MARKET_ACCESS": "Target market has favorable geographic accessibility.",
    "ROBUST_SUPPLY": "Reliable supply ecosystem with strong local raw material accessibility."
}

NEGATIVE_FACTOR_TEMPLATES = {
    "SUPPLY_FRICTION": "Supply ecosystem introduces procurement or logistics friction.",
    "HIGH_SEASONALITY": "Demand has significant seasonal variation.",
    "HIGH_COMPETITION_PRESSURE": "Elevated competitive pressure in the catchment may constrain initial market share.",
    "INFRASTRUCTURE_GAPS": "Unmet infrastructure requirements create operational constraints.",
    "MARKET_SATURATION": "Catchment demonstrates high market saturation.",
    "PROXY_HEAVY_EVIDENCE": "Part of the analysis relies on proxy-based market evidence."
}
