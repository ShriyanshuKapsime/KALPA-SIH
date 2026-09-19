"""
Constants, centralized category weights, and benchmark reference thresholds for Stage 11 Risk Engine.
"""

RISK_WEIGHT_FINANCIAL = 0.25
RISK_WEIGHT_MARKET = 0.20
RISK_WEIGHT_OPERATIONAL = 0.15
RISK_WEIGHT_SEASONAL = 0.10
RISK_WEIGHT_SUPPLY_CHAIN = 0.10
RISK_WEIGHT_COMPETITION = 0.10
RISK_WEIGHT_INFRASTRUCTURE = 0.10

SEVERITY_THRESHOLD_CRITICAL = 0.85
SEVERITY_THRESHOLD_HIGH = 0.65
SEVERITY_THRESHOLD_MEDIUM = 0.40

# Official Institutional Benchmark Reference Norms
BENCHMARK_NORMS = {
    "FINANCIAL_DSCR_MINIMUM": {
        "name": "Minimum DSCR Threshold",
        "value": "1.15x",
        "source": "RBI / SIDBI MSME Lending Standards",
        "critical_below": 1.15,
        "high_below": 1.35,
        "medium_below": 1.75
    },
    "FINANCIAL_BREAK_EVEN_MAX": {
        "name": "Maximum Safe Break-Even Capacity",
        "value": "70.0%",
        "source": "NABARD / MoMSME Project Appraisal Manual",
        "critical_above": 80.0,
        "high_above": 70.0
    },
    "MARKET_OPPORTUNITY_SCORE_MIN": {
        "name": "Stage 8 Opportunity Index Threshold",
        "value": "60.0%",
        "source": "KALPA Stage 8 Opportunity Synthesis"
    },
    "COMPETITION_SATURATION_MAX": {
        "name": "Competitor Clustering Saturation Limit",
        "value": "5 operating units in 5km catchment radius",
        "source": "NCAER Catchment Density Norms"
    },
    "SEASONAL_VOLATILITY_MAX": {
        "name": "Seasonal Revenue Multiplier Variance",
        "value": "0.30 variance threshold",
        "source": "NABARD Commodity Seasonal Cycle Catalog"
    }
}
