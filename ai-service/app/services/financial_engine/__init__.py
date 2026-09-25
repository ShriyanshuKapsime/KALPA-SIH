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
from app.services.financial_engine.intelligence import (
    FinancialArchetype,
    archetype_registry,
    ArchetypeRegistry,
    DriverRegistry,
    DriverDefinition,
    driver_registry,
    AssumptionResolver,
    assumption_resolver,
    ResolvedAssumption,
    SourceType,
    AssumptionStatus,
    AssumptionType,
    QuestionEngine,
    question_engine,
    RequiredUserInput,
    ProvenanceTracker,
    provenance_tracker,
    Provenance,
    FoundationStatus,
    EvidenceResolver,
    evidence_resolver,
)
from app.services.financial_engine.calculation import (
    CALCULATION_REGISTRY,
)
from app.services.financial_engine.compatibility import (
    legacy_adapter,
    LegacyAdapter,
)
from app.services.financial_engine.project_cost import (
    DerivationEngine,
    derivation_engine,
    CircularDependencyError,
    WorkingCapitalEngine,
    working_capital_engine,
    CapExEngine,
    capex_engine,
    ProjectCostReconciler,
    project_cost_reconciler,
    ProjectCostEngine,
    project_cost_engine,
)

# Aliases for backward compatibility
FinancialDriver = DriverDefinition
UserQuestion = RequiredUserInput

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
    "ENGINE_NAME",
    # Milestone 1: Financial Intelligence Foundation exports
    "FinancialArchetype",
    "archetype_registry",
    "ArchetypeRegistry",
    "DriverRegistry",
    "DriverDefinition",
    "FinancialDriver",
    "driver_registry",
    "AssumptionResolver",
    "assumption_resolver",
    "ResolvedAssumption",
    "SourceType",
    "AssumptionStatus",
    "AssumptionType",
    "QuestionEngine",
    "question_engine",
    "RequiredUserInput",
    "UserQuestion",
    "ProvenanceTracker",
    "provenance_tracker",
    "Provenance",
    "FoundationStatus",
    "EvidenceResolver",
    "evidence_resolver",
    "CALCULATION_REGISTRY",
    "legacy_adapter",
    "LegacyAdapter",
    # Milestone 2: Automated Project Cost & Working Capital Engine exports
    "DerivationEngine",
    "derivation_engine",
    "CircularDependencyError",
    "WorkingCapitalEngine",
    "working_capital_engine",
    "CapExEngine",
    "capex_engine",
    "ProjectCostReconciler",
    "project_cost_reconciler",
    "ProjectCostEngine",
    "project_cost_engine",
    # Milestone 6: Bankable DPR Financial Packager exports
    "DPRPackager",
    "dpr_packager",
    "DPRFinancialPackage",
    "DPRSection",
    "CMAStatementPackage",
    "DataCompletenessPackage",
    "format_inr",
    "format_percentage",
    "format_ratio",
]
from app.services.financial_engine.dpr_packager import (
    DPRPackager,
    dpr_packager,
    DPRFinancialPackage,
    DPRSection,
    CMAStatementPackage,
    DataCompletenessPackage,
    format_inr,
    format_percentage,
    format_ratio,
)


