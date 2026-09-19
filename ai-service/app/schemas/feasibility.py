"""
Pydantic Schemas for Stage 12: Feasibility Engine.
Coordinates multivariate venture viability scoring combining Stage 8 Opportunity,
Stage 9 Finance, Stage 10 Entrepreneur Profile, Stage 11 Risk Analysis, Critical Gates,
ML model slots, Dynamic SWOT, and Pivot Advisory.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class FeasibilityFeatureItem(BaseModel):
    """Individual feature item with exact upstream provenance."""
    value: Any = None
    source_stage: str
    source_field: str
    confidence: float = 1.0
    status: str = "VERIFIED"  # VERIFIED, CALCULATED, USER_INPUT, BENCHMARK, DATA_GAP


class FeasibilityFeatureVector(BaseModel):
    """Canonical normalized feature vector consumed by the Feasibility Engine."""
    # Market Features (Stage 8 + Stage 6)
    market_opportunity_score: FeasibilityFeatureItem
    demand_index: FeasibilityFeatureItem
    competition_pressure: FeasibilityFeatureItem
    market_accessibility: FeasibilityFeatureItem
    market_capacity: FeasibilityFeatureItem

    # Financial Features (Stage 9)
    financial_viability_score: FeasibilityFeatureItem
    project_cost: FeasibilityFeatureItem
    loan_amount: FeasibilityFeatureItem
    emi: FeasibilityFeatureItem
    dscr: FeasibilityFeatureItem
    break_even_percentage: FeasibilityFeatureItem
    cash_flow_status: FeasibilityFeatureItem

    # Entrepreneur Features (Stage 10)
    entrepreneur_readiness_score: FeasibilityFeatureItem
    skills_score: FeasibilityFeatureItem
    experience_score: FeasibilityFeatureItem
    training_score: FeasibilityFeatureItem
    resources_score: FeasibilityFeatureItem
    operational_score: FeasibilityFeatureItem

    # Risk Features (Stage 11)
    overall_risk_score: FeasibilityFeatureItem
    overall_risk_severity: FeasibilityFeatureItem
    financial_risk: FeasibilityFeatureItem
    market_risk: FeasibilityFeatureItem
    operational_risk: FeasibilityFeatureItem
    seasonal_risk: FeasibilityFeatureItem
    supply_chain_risk: FeasibilityFeatureItem
    competition_risk: FeasibilityFeatureItem
    infrastructure_risk: FeasibilityFeatureItem

    # Metadata & Quality
    critical_constraints_count: int = 0
    evidence_quality_score: float = 1.0
    raw_vector_summary: Dict[str, Any] = Field(default_factory=dict)


class CriticalGateResult(BaseModel):
    """Evaluation result for an essential constraint / critical gate."""
    gate_id: str  # FINANCIAL_CAPACITY, CRITICAL_INFRASTRUCTURE, MARKET_CAPACITY, STATUTORY_COMPLIANCE
    name: str
    status: str  # PASS, CAUTION, RESTRICT
    evidence: Union[str, List[str]]
    threshold: str
    actual_value: str
    explanation: str
    source_stage: str


class PillarScore(BaseModel):
    """Evaluated score and weighted contribution for each of the 4 core pillars."""
    pillar: str  # MARKET_OPPORTUNITY, FINANCIAL_VIABILITY, ENTREPRENEUR_READINESS, RISK_RESILIENCE
    title: str
    score: float = 0.0  # 0 to 100
    weight: float = 0.25  # Centralized weight
    weighted_contribution: float = 0.0  # score * weight
    source_stage: str
    status: str = "ADEQUATE"  # STRONG, ADEQUATE, CAUTION, RESTRICT, DATA_GAP
    confidence: float = 1.0
    explanation: str
    key_inputs: Dict[str, Any] = Field(default_factory=dict)
    formula: str = ""


class SWOTItem(BaseModel):
    """Evidence-grounded SWOT item."""
    title: str
    description: str
    source_stage: str
    evidence: Optional[str] = None
    severity_or_impact: str = "HIGH"  # HIGH, MEDIUM, LOW


class DynamicSWOTResponse(BaseModel):
    """Dynamic evidence-grounded SWOT analysis."""
    strengths: List[SWOTItem] = Field(default_factory=list)
    weaknesses: List[SWOTItem] = Field(default_factory=list)
    opportunities: List[SWOTItem] = Field(default_factory=list)
    threats: List[SWOTItem] = Field(default_factory=list)


class PivotCandidate(BaseModel):
    """Alternative micro-enterprise recommendation tailored to entrepreneur capability & capital."""
    business_id: str
    business_name: str
    sector: str
    category: str
    pivot_reason: str
    skill_fit_percentage: float
    capital_requirement: float
    capital_fit: str  # WITHIN_BUDGET, MINIMAL_GAP, EXCEEDS_BUDGET
    market_rationale: str
    key_advantages: List[str] = Field(default_factory=list)


class FeasibilityEvaluationRequest(BaseModel):
    """Request payload for Feasibility Analysis."""
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None
    location_profile: Optional[Dict[str, Any]] = None
    opportunity_result: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    entrepreneur_readiness: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None


class FeasibilityAnalysisResponse(BaseModel):
    """Comprehensive Stage 12 Feasibility Outcome."""
    analysis_id: str
    session_id: str
    business_id: Optional[str] = None
    business_name: str
    location_summary: str
    overall_feasibility_score: float  # 0 to 100
    decision: str  # VIABLE, VIABLE_WITH_CAUTION, CONDITIONALLY_VIABLE, NOT_FEASIBLE, DATA_INSUFFICIENT
    recommendation: str  # YES, CONDITIONAL, NO
    confidence_score: float  # 0.0 to 1.0

    # ML Model Slot Interface Output
    ml_prediction: Dict[str, Any] = Field(
        default_factory=lambda: {
            "prediction": None,
            "probability": None,
            "model_version": None,
            "status": "NOT_CONFIGURED",
            "explanation": "ML prediction model is not configured. 100% deterministic evaluation engine is active."
        }
    )

    # 4 Core Analytical Pillars
    pillar_scores: Dict[str, PillarScore] = Field(default_factory=dict)

    # Hard Constraints / Critical Gates
    critical_gates: List[CriticalGateResult] = Field(default_factory=list)

    # Explainability & Decision Drivers
    positive_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    key_constraints: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)

    # Branching Outcomes
    dynamic_swot: DynamicSWOTResponse = Field(default_factory=DynamicSWOTResponse)
    pivot_recommendations: List[PivotCandidate] = Field(default_factory=list)

    # Audit & Provenance Trace
    calculation_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    data_completeness: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str = "FEASIBILITY_COMPLETE"
