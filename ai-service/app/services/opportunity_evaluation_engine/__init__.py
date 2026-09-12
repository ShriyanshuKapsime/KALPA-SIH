"""
Stage 8: Opportunity Evaluation Engine Package.
Exports the OpportunityEvaluationEngine class, singleton instance, and configuration constants.
"""
from app.services.opportunity_evaluation_engine.constants import (
    OPPORTUNITY_WEIGHTS,
    SUPPLY_WEIGHTS,
    OPPORTUNITY_LEVEL_THRESHOLDS,
    DEMAND_SIGNAL_THRESHOLDS,
    CONSTRAINT_PENALTIES,
    POSITIVE_FACTOR_TEMPLATES,
    NEGATIVE_FACTOR_TEMPLATES
)
from app.services.opportunity_evaluation_engine.engine import (
    OpportunityEvaluationEngine,
    opportunity_evaluation_engine
)
from app.schemas.opportunity_evaluation import (
    OpportunityLevel,
    DemandSourceType,
    ConstraintSeverity,
    OpportunityResult,
    OpportunityEvaluationRequest,
    OpportunityEvaluationResponse
)

__all__ = [
    "OpportunityEvaluationEngine",
    "opportunity_evaluation_engine",
    "OPPORTUNITY_WEIGHTS",
    "SUPPLY_WEIGHTS",
    "OPPORTUNITY_LEVEL_THRESHOLDS",
    "DEMAND_SIGNAL_THRESHOLDS",
    "CONSTRAINT_PENALTIES",
    "POSITIVE_FACTOR_TEMPLATES",
    "NEGATIVE_FACTOR_TEMPLATES",
    "OpportunityLevel",
    "DemandSourceType",
    "ConstraintSeverity",
    "OpportunityResult",
    "OpportunityEvaluationRequest",
    "OpportunityEvaluationResponse"
]
