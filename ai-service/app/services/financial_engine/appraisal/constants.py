"""
Centralized appraisal thresholds and constants for M4 Banking Appraisal & Viability Engine.
Standardizes underwriting benchmarks across liquidity, debt service, leverage, and break-even.
"""

# DSCR / Debt Service Coverage Thresholds
DSCR_BENCHMARK = 1.25       # Minimum institutional underwriting benchmark
DSCR_MINIMUM = 1.00         # Hard coverage floor (below 1.0 indicates cash deficit)
DSCR_ROBUST = 1.50          # Strong institutional buffer

# Liquidity / Working Capital Thresholds
LIQUIDITY_CURRENT_RATIO_ADEQUATE = 1.33   # Tandon Committee / Banking Norm
LIQUIDITY_CURRENT_RATIO_TIGHT = 1.00      # Working capital break-even (CA == CL)

# Leverage / Capital Structure Thresholds
LEVERAGE_DER_HIGH = 4.00       # Excessive leverage threshold
LEVERAGE_DER_ELEVATED = 3.00   # Elevated leverage warning threshold

# Break-Even Utilization Thresholds
BREAK_EVEN_UTILIZATION_HIGH = 80.0        # High operational gearing / sensitivity threshold
BREAK_EVEN_UTILIZATION_MODERATE = 70.0    # Moderate operational risk threshold
