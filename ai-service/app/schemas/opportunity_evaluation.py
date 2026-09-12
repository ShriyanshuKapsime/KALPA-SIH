"""
Pydantic Schemas for Stage 8: Opportunity Evaluation Engine.
Defines data models for request ingestion, normalized component inputs,
deterministic opportunity synthesis, constraint evaluation, explainable provenance,
and downstream Feasibility Engine handover.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class OpportunityLevel(str, Enum):
    HIGH_OPPORTUNITY = "HIGH_OPPORTUNITY"
    MODERATE_OPPORTUNITY = "MODERATE_OPPORTUNITY"
    LIMITED_OPPORTUNITY = "LIMITED_OPPORTUNITY"
    LOW_OPPORTUNITY = "LOW_OPPORTUNITY"


class DemandSourceType(str, Enum):
    STAGE_7_ML = "STAGE_7_ML"
    STAGE_6_DETERMINISTIC_EVIDENCE = "STAGE_6_DETERMINISTIC_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"


class ConstraintSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# -----------------------------------------------------------------------------
# Component Models
# -----------------------------------------------------------------------------

class DemandScoreDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = "STAGE_6_DETERMINISTIC_EVIDENCE"
    level: str = "HIGH"
    fallback_used: bool = False


class CompetitionOpportunityDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    pressure_score: float = Field(default=0.0, ge=0.0, le=1.0)
    pressure_level: str = "LOW"
    direct_competitors: int = 0


class InfrastructureOpportunityDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    readiness: str = "AVAILABLE"
    readiness_score: float = 1.0
    critical_gaps_count: int = 0
    gap_penalty: float = 0.0


class SupplyOpportunityDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    input_coverage_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    accessibility: str = "HIGH"


class MarketAccessOpportunityDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    geographic_accessibility_score: float = 1.0
    accessibility: str = "HIGH"


class MarketCapacityOpportunityDetail(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    net_capacity_score: float = 1.0
    status: str = "AVAILABLE"
    capacity_signal: str = "EXPANSION_CAPACITY"


class OpportunityComponentScores(BaseModel):
    demand: DemandScoreDetail
    competition_opportunity: CompetitionOpportunityDetail
    infrastructure: InfrastructureOpportunityDetail
    supply_ecosystem: SupplyOpportunityDetail
    market_access: MarketAccessOpportunityDetail
    market_capacity: MarketCapacityOpportunityDetail


class DemandSourceMetadata(BaseModel):
    type: DemandSourceType = DemandSourceType.STAGE_6_DETERMINISTIC_EVIDENCE
    stage_7_available: bool = False
    fallback_used: bool = True
    confidence: float = 0.85
    details: Optional[Dict[str, Any]] = None


class OpportunityConstraint(BaseModel):
    constraint_id: str
    severity: ConstraintSeverity = ConstraintSeverity.MODERATE
    component: str
    description: str
    blocking: bool = False
    score_impact: float = 0.0


class OpportunityCalculationRecord(BaseModel):
    indicator: str
    formula: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    intermediate_steps: List[str] = Field(default_factory=list)
    output_value: float
    confidence: float = 0.85


class OpportunityProvenance(BaseModel):
    formula: str
    weights: Dict[str, float]
    component_scores: Dict[str, float]
    constraint_adjustments: List[Dict[str, Any]] = Field(default_factory=list)
    final_score: float
    classification_method: str = "deterministic_thresholds"
    level_override: bool = False
    override_reason: Optional[str] = None
    step_records: List[OpportunityCalculationRecord] = Field(default_factory=list)


class Stage8WorkflowState(BaseModel):
    stage: int = 8
    state: str = "MARKET_OPPORTUNITY_EVALUATED"
    status: str = "complete"  # complete | complete_with_constraints


class OpportunityEvidenceQuality(BaseModel):
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    proxy_dependency: float = Field(default=0.0, ge=0.0, le=1.0)
    data_gaps: List[Dict[str, Any]] = Field(default_factory=list)


class Stage8NextStageContract(BaseModel):
    stage: Optional[int] = None
    component: str = "FEASIBILITY_ENGINE"
    input_contract: str = "opportunity_result"


class Stage8ExecutionMetadata(BaseModel):
    engine: str = "deterministic_opportunity_evaluation_engine"
    engine_version: str = "1.0.0"
    llm_used: bool = False
    stage_7_ml_used: bool = False
    demand_fallback_used: bool = True
    status: str = "SUCCESS"
    execution_time_seconds: float = 0.0


# -----------------------------------------------------------------------------
# Top-Level Opportunity Result & Request/Response Models
# -----------------------------------------------------------------------------

class OpportunityResult(BaseModel):
    market_opportunity_score: float = Field(..., ge=0.0, le=1.0)
    level: OpportunityLevel
    demand_source: DemandSourceMetadata
    component_scores: OpportunityComponentScores
    positive_factors: List[str] = Field(default_factory=list)
    negative_factors: List[str] = Field(default_factory=list)
    constraints: List[OpportunityConstraint] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    level_override: bool = False
    override_reason: Optional[str] = None


class OpportunityEvaluationRequest(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_context: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    market_intelligence: Optional[Dict[str, Any]] = None  # Full Stage 6 output or components
    demand_prediction: Optional[Dict[str, Any]] = None   # Stage 7 ML model output (optional)


class OpportunityEvaluationResponse(BaseModel):
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str
    workflow: Stage8WorkflowState = Field(default_factory=Stage8WorkflowState)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    opportunity_result: OpportunityResult
    evidence_quality: OpportunityEvidenceQuality
    calculation_provenance: OpportunityProvenance
    next_stage: Stage8NextStageContract = Field(default_factory=Stage8NextStageContract)
    execution_metadata: Stage8ExecutionMetadata = Field(default_factory=Stage8ExecutionMetadata)
