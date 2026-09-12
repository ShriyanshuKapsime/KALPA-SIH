"""
Constants, Scheme Rules, and Configuration Parameters for Stage 9: Financial Engine.
Centralized source of truth for MSME scheme rules, moratorium policies,
DSCR thresholds, financial health scoring weights, and viability criteria.
"""
from typing import Dict, Any

# -----------------------------------------------------------------------------
# 1. Centrally Configured Scheme Rules (Source of Truth)
# -----------------------------------------------------------------------------

SCHEME_RULES: Dict[str, Dict[str, Any]] = {
    "MICRO_FINANCE_SCHEME": {
        "scheme_id": "MICRO_FINANCE_SCHEME",
        "scheme_name": "Micro Enterprise Finance Scheme (PMMY Shishu / Kishore Benchmark)",
        "condition_description": "Project cost <= 1,40,000 INR",
        "min_project_cost": 0.0,
        "max_project_cost": 140000.0,
        "margin_ratio": 0.10,          # 10% entrepreneur contribution
        "loan_ratio": 0.90,            # 90% debt financing
        "maximum_loan": 125000.0,      # Strict cap of 1,25,000 INR
        "annual_interest_rate": 0.065, # 6.5% annual rate
        "tenure_months": 36,           # 3-year repayment tenure
        "moratorium_months": 3,        # 3 months moratorium
        "moratorium_interest_mode": "INTEREST_ONLY",
        "target_segment": "Micro units, rural artisan workshops, nano-enterprises",
        "eligibility_criteria": [
            "Indian citizen with valid Aadhaar/PAN",
            "No existing defaults with commercial or regional rural banks",
            "Business activity falls under non-farm micro-enterprise sector"
        ]
    },
    "TERM_LOAN_SCHEME": {
        "scheme_id": "TERM_LOAN_SCHEME",
        "scheme_name": "MSME Term Loan & Working Capital Facility (CGTMSE / PMEGP Benchmark)",
        "condition_description": "1,40,000 < Project cost <= 50,00,000 INR",
        "min_project_cost": 140000.01,
        "max_project_cost": 5000000.0,
        "margin_ratio": 0.10,          # 10% entrepreneur contribution
        "loan_ratio": 0.90,            # 90% debt financing
        "maximum_loan": 4500000.0,     # Strict cap of 45,00,000 INR
        "annual_interest_rate": 0.080, # 8.0% annual rate
        "tenure_months": 84,           # 7-year repayment tenure
        "moratorium_months": 6,        # 6 months moratorium
        "moratorium_interest_mode": "INTEREST_ONLY",
        "target_segment": "Small manufacturing, processing units, commercial retail & services",
        "eligibility_criteria": [
            "Indian citizen aged 18+ with business registration / Udyam Certificate",
            "Viable project profile with compliant land/premises lease or ownership",
            "Satisfactory credit standing with zero non-performing assets"
        ]
    }
}

# Supported Max Boundary
MAX_SUPPORTED_PROJECT_COST = 5000000.0  # 50 Lakh INR

# -----------------------------------------------------------------------------
# 2. Moratorium Calculation Modes
# -----------------------------------------------------------------------------

MORATORIUM_MODES = {
    "INTEREST_ONLY": "Interest serviced monthly during moratorium phase (Principal balance unchanged).",
    "INTEREST_CAPITALIZED": "Interest accumulated and capitalized into principal balance at end of moratorium.",
    "FULL_PAYMENT_HOLIDAY": "No payment during moratorium; accumulated interest amortized across remaining tenure."
}

DEFAULT_MORATORIUM_MODE = "INTEREST_ONLY"

# -----------------------------------------------------------------------------
# 3. Debt Service Coverage Ratio (DSCR) Thresholds
# -----------------------------------------------------------------------------

DSCR_THRESHOLDS = {
    "STRONG": {
        "min": 1.50,
        "label": "Strong Coverage",
        "description": "Operating cash flow exceeds periodic debt service by 50% or more."
    },
    "ADEQUATE": {
        "min": 1.20,
        "max": 1.50,
        "label": "Adequate Coverage",
        "description": "Operating cash flow comfortably covers periodic debt service with 20-50% buffer."
    },
    "WEAK": {
        "max": 1.20,
        "label": "Weak / High Risk Coverage",
        "description": "Operating cash flow provides insufficient buffer for debt obligations."
    }
}

# -----------------------------------------------------------------------------
# 4. Financial Health Score Weights (Sum strictly to 1.0)
# -----------------------------------------------------------------------------

FINANCIAL_HEALTH_WEIGHTS = {
    "margin_adequacy": 0.25,          # Ability to fund required 10% equity without stress
    "working_capital_adequacy": 0.20, # Working capital allocation relative to benchmark requirement
    "debt_service_capacity": 0.25,    # DSCR / debt-to-income sustainability
    "cash_flow_strength": 0.15,       # Net positive cash flow after debt service
    "break_even_strength": 0.15       # Low break-even revenue requirement (< 65% capacity)
}

# Sanity assertion
assert abs(sum(FINANCIAL_HEALTH_WEIGHTS.values()) - 1.0) < 1e-6, "Financial health weights must sum to 1.0"

# -----------------------------------------------------------------------------
# 5. Default Fallback Benchmarks when specific enterprise data is unavailable
# -----------------------------------------------------------------------------

DEFAULT_CAPITAL_ALLOCATION = {
    "capex_percentage": 70.0,
    "working_capital_percentage": 30.0
}

# Calculation Metadata Version
CALCULATION_VERSION = "stage9_v1"
ENGINE_NAME = "deterministic_financial_engine"
