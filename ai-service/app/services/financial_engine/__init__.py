"""
Stage 9: Financial Engine Package.
Exports the FinancialEngine singleton and sub-engines.
"""
from app.services.financial_engine.constants import (
    SCHEME_RULES,
    MORATORIUM_MODES,
    DEFAULT_MORATORIUM_MODE,
    DSCR_THRESHOLDS,
    FINANCIAL_HEALTH_WEIGHTS,
    CALCULATION_VERSION,
    ENGINE_NAME
)
from app.services.financial_engine.benchmark_adapter import (
    financial_benchmark_adapter,
    FinancialBenchmarkAdapter,
    BenchmarkFinancialData
)
from app.services.financial_engine.loan_calculator import (
    loan_calculator,
    LoanCalculator
)
from app.services.financial_engine.amortization import (
    amortization_engine,
    AmortizationEngine
)
from app.services.financial_engine.capital_allocation import (
    capital_allocation_engine,
    CapitalAllocationEngine
)
from app.services.financial_engine.profitability import (
    profitability_engine,
    ProfitabilityEngine
)
from app.services.financial_engine.cash_flow import (
    cash_flow_engine,
    CashFlowEngine
)
from app.services.financial_engine.break_even import (
    break_even_engine,
    BreakEvenEngine
)
from app.services.financial_engine.viability import (
    viability_engine,
    ViabilityEngine
)
from app.services.financial_engine.engine import (
    financial_engine,
    FinancialEngine
)

__all__ = [
    "financial_engine",
    "FinancialEngine",
    "financial_benchmark_adapter",
    "FinancialBenchmarkAdapter",
    "BenchmarkFinancialData",
    "loan_calculator",
    "LoanCalculator",
    "amortization_engine",
    "AmortizationEngine",
    "capital_allocation_engine",
    "CapitalAllocationEngine",
    "profitability_engine",
    "ProfitabilityEngine",
    "cash_flow_engine",
    "CashFlowEngine",
    "break_even_engine",
    "BreakEvenEngine",
    "viability_engine",
    "ViabilityEngine",
    "SCHEME_RULES",
    "MORATORIUM_MODES",
    "DEFAULT_MORATORIUM_MODE",
    "DSCR_THRESHOLDS",
    "FINANCIAL_HEALTH_WEIGHTS",
    "CALCULATION_VERSION",
    "ENGINE_NAME"
]
