"""
Milestone 5: Stress Testing, Scheme Routing & Financing Optimizer Package.
Deterministic decision layer for downside resilience, government scheme matching,
and bankable financing structure optimization.
"""
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode
from app.services.financial_engine.optimizer.m5_config import (
    POLICY_VERSION,
    MODEL_VERSION,
    POLICY_STRESS_PARAMETERS,
    DSCR_RESILIENCE_BENCHMARK,
    DSCR_RESILIENCE_MINIMUM,
    CURRENT_RATIO_RESILIENCE_MINIMUM,
    CASH_BUFFER_RESILIENCE_MONTHS,
    BREAK_EVEN_MAX_UTILIZATION
)
from app.services.financial_engine.optimizer.m5_schema import (
    StressScenarioType,
    ScenarioSource,
    ResilienceStatus,
    SchemeEligibilityStatus,
    M5ValidationState,
    M5ProvenanceRecord,
    M5ValidationCheck,
    M5ValidationResult,
    StressScenarioResult,
    SchemeRoutingOption,
    PromoterContributionAnalysisResult,
    FinancingGapAnalysisResult,
    TenureOptionResult,
    FinancingStructureCandidate,
    ResilienceComparisonRow,
    ResilienceAnalysisResult,
    M5DprFinancingSummary,
    M5OptimizationResult
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder
from app.services.financial_engine.optimizer.stress_scenarios import (
    stress_scenario_generator,
    StressScenarioGenerator,
    ScenarioSpecification
)
from app.services.financial_engine.optimizer.stress_engine import (
    stress_engine,
    StressEngine
)
from app.services.financial_engine.optimizer.resilience_analysis import (
    resilience_analysis_engine,
    ResilienceAnalysisEngine
)
from app.services.financial_engine.optimizer.scheme_router import (
    scheme_router,
    SchemeRouter
)
from app.services.financial_engine.optimizer.promoter_contribution_analysis import (
    promoter_contribution_analysis_engine,
    PromoterContributionAnalysisEngine
)
from app.services.financial_engine.optimizer.financing_feasibility import (
    financing_feasibility_engine,
    FinancingFeasibilityEngine
)
from app.services.financial_engine.optimizer.tenure_analysis import (
    tenure_analysis_engine,
    TenureAnalysisEngine
)
from app.services.financial_engine.optimizer.financing_options import (
    financing_options_generator,
    FinancingOptionsGenerator
)
from app.services.financial_engine.optimizer.financing_optimizer import (
    financing_optimizer,
    FinancingOptimizer
)
from app.services.financial_engine.optimizer.m5_validation import (
    m5_validation_engine,
    M5ValidationEngine
)
from app.services.financial_engine.optimizer.m5_engine import (
    m5_engine,
    M5Engine
)

__all__ = [
    "M5ReasonCode",
    "POLICY_VERSION",
    "MODEL_VERSION",
    "POLICY_STRESS_PARAMETERS",
    "DSCR_RESILIENCE_BENCHMARK",
    "DSCR_RESILIENCE_MINIMUM",
    "CURRENT_RATIO_RESILIENCE_MINIMUM",
    "CASH_BUFFER_RESILIENCE_MONTHS",
    "BREAK_EVEN_MAX_UTILIZATION",
    "StressScenarioType",
    "ScenarioSource",
    "ResilienceStatus",
    "SchemeEligibilityStatus",
    "M5ValidationState",
    "M5ProvenanceRecord",
    "M5ValidationCheck",
    "M5ValidationResult",
    "StressScenarioResult",
    "SchemeRoutingOption",
    "PromoterContributionAnalysisResult",
    "FinancingGapAnalysisResult",
    "TenureOptionResult",
    "FinancingStructureCandidate",
    "ResilienceComparisonRow",
    "ResilienceAnalysisResult",
    "M5DprFinancingSummary",
    "M5OptimizationResult",
    "M5ProvenanceBuilder",
    "stress_scenario_generator",
    "StressScenarioGenerator",
    "ScenarioSpecification",
    "stress_engine",
    "StressEngine",
    "resilience_analysis_engine",
    "ResilienceAnalysisEngine",
    "scheme_router",
    "SchemeRouter",
    "promoter_contribution_analysis_engine",
    "PromoterContributionAnalysisEngine",
    "financing_feasibility_engine",
    "FinancingFeasibilityEngine",
    "tenure_analysis_engine",
    "TenureAnalysisEngine",
    "financing_options_generator",
    "FinancingOptionsGenerator",
    "financing_optimizer",
    "FinancingOptimizer",
    "m5_validation_engine",
    "M5ValidationEngine",
    "m5_engine",
    "M5Engine"
]
