"""
Pydantic Schemas for Stage 13: Dynamic SWOT Agent.
Defines strict data contracts for evidence-grounded SWOT generation,
cross-engine synthesis, strategic summaries, actionable recommendations,
provenance tracking, generation metadata, and fallback/gating statuses.
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class SWOTEvidenceRef(BaseModel):
    """Provenance tracking link connecting a SWOT item to upstream engine evidence."""
    source_stage: str = Field(..., description="Stage producing the evidence, e.g. STAGE_6, STAGE_8, STAGE_9, STAGE_10, STAGE_11, STAGE_12")
    source_field: str = Field("general", description="Specific field path in upstream stage, e.g. financial_analysis.dscr or entrepreneur_readiness.skills")
    value: Any = Field(None, description="Actual measured or evaluated value from upstream engine")
    confidence: float = Field(0.85, ge=0.0, le=1.0, description="Confidence score associated with this evidence point")


class RoadmapPhase(BaseModel):
    """Phased implementation step in the strategic roadmap."""
    phase: str = Field(..., description="e.g. 0-30 days, 30-90 days, 90+ days")
    actions: List[str] = Field(default_factory=list, description="Action items for this phase")


class PriorityAction(BaseModel):
    """Actionable recommendation prioritized from upstream synthesis."""
    id: Optional[str] = Field(None, description="Unique action identifier e.g. SP-001, PA-001")
    action: str = Field(..., description="Concrete practical action step for the entrepreneur")
    reason: str = Field(..., description="Why this action is critical based on evidence")
    priority: str = Field("HIGH", description="HIGH | MEDIUM | LOW")
    source_stage: str = Field("STAGE_10", description="Upstream stage that triggered this action")
    linked_dimension: Optional[str] = Field(None, description="market | finance | entrepreneur | risk | feasibility")


class SWOTItem(BaseModel):
    """An individual Strength, Weakness, Opportunity, or Threat item."""
    id: str = Field(..., description="Unique item identifier, e.g. ST-001, WK-001, OP-001, TH-001")
    category: str = Field("STRENGTH", description="Category: STRENGTH | WEAKNESS | OPPORTUNITY | THREAT")
    title: str = Field(..., description="Concise, punchy heading for rural entrepreneur")
    explanation: str = Field("", description="Clear concise explanation (1-3 sentences)")
    statement: str = Field("", description="Clear explanation in accessible language (backward compatibility)")
    why_it_matters: str = Field("", description="Strategic implication explaining why this factor is important")
    business_impact: Optional[str] = Field(None, description="Operational or financial impact on the business")
    action: Optional[str] = Field(None, description="Value-capture action step for opportunities")
    mitigation: Optional[str] = Field(None, description="Risk mitigation strategy for threats")
    evidence: List[Union[str, SWOTEvidenceRef]] = Field(default_factory=list, description="Upstream evidence citations supporting this item")
    source_stage: str = Field("STAGE_12", description="Primary upstream stage generating this factor")
    confidence: float = Field(0.85, ge=0.0, le=1.0, description="Overall confidence in this assessment")
    priority: str = Field("HIGH", description="HIGH | MEDIUM | LOW priority/impact level")
    data_status: str = Field("KNOWN", description="KNOWN | INFERRED | DATA_GAP")

    def model_post_init(self, __context: Any) -> None:
        """Synchronize statement and explanation fields."""
        if not self.statement and self.explanation:
            self.statement = self.explanation
        elif not self.explanation and self.statement:
            self.explanation = self.statement
        if not self.why_it_matters and self.statement:
            self.why_it_matters = self.statement
        if self.business_impact and not self.why_it_matters:
            self.why_it_matters = self.business_impact


class SWOTCategoryBreakdown(BaseModel):
    """Grouped SWOT quadrants, priority actions, and executive synthesis."""
    executive_summary: Optional[str] = Field(None, description="Concise plain-language executive summary")
    strengths: List[SWOTItem] = Field(default_factory=list)
    weaknesses: List[SWOTItem] = Field(default_factory=list)
    opportunities: List[SWOTItem] = Field(default_factory=list)
    threats: List[SWOTItem] = Field(default_factory=list)
    priority_actions: List[PriorityAction] = Field(default_factory=list)
    strategic_priorities: List[PriorityAction] = Field(default_factory=list)
    roadmap: List[RoadmapPhase] = Field(default_factory=list)
    strategic_direction: Optional[str] = Field(None, description="Concise plain-language strategic direction")
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class SWOTGenerationMeta(BaseModel):
    """Execution metadata indicating whether Sarvam AI LLM or deterministic fallback was used."""
    mode: str = Field("SARVAM_LLM", description="SARVAM_LLM | DETERMINISTIC_FALLBACK")
    model: str = Field("sarvam-105b", description="Model identifier")
    llm_status: str = Field("success", description="success | timeout | parse_error | unavailable | http_error")
    execution_time_ms: Optional[float] = None


class StrategicSummary(BaseModel):
    """Executive strategic interpretation synthesizing all 4 SWOT dimensions."""
    business_position: str = Field(..., description="Overall strategic posture of the venture")
    key_advantage: str = Field(..., description="Primary structural or operational advantage")
    main_constraint: str = Field(..., description="Primary bottleneck or limiting factor")
    biggest_opportunity: str = Field(..., description="Most lucrative market expansion or efficiency opportunity")
    biggest_threat: str = Field(..., description="Most critical risk factor that could derail operations")


class SWOTRecommendation(BaseModel):
    """Evidence-linked strategic recommendation."""
    title: str = Field(...)
    action: str = Field(..., description="Concrete practical action step for the entrepreneur")
    reason: str = Field(..., description="Reasoning rooted in upstream analysis")
    priority: str = Field("HIGH", description="HIGH | MEDIUM | LOW")
    linked_factors: List[str] = Field(default_factory=list, description="IDs of linked SWOT items or factor names")
    source_stages: List[str] = Field(default_factory=list, description="Stages that informed this recommendation")


class ImmediateAction(BaseModel):
    """Immediate next step priority."""
    action: str = Field(..., description="What the entrepreneur must do next")
    why: str = Field(..., description="Why this action is urgent")
    priority: str = Field("HIGH", description="HIGH | MEDIUM | LOW")


class SWOTEvidenceSummary(BaseModel):
    """High-level synthesis of upstream evidence status across the 5 pillars."""
    market: str = Field("", description="Summary of Stage 6/8 opportunity evidence")
    financial: str = Field("", description="Summary of Stage 9 financial metrics")
    entrepreneur: str = Field("", description="Summary of Stage 10 readiness and capacity")
    risk: str = Field("", description="Summary of Stage 11 multi-vector risk exposure")
    feasibility: str = Field("", description="Summary of Stage 12 feasibility verdict")


class ModelMetadata(BaseModel):
    """LLM execution metadata."""
    provider: str = Field("sarvam")
    model: str = Field("sarvam-105b")
    version: str = Field("1.0.0")
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[float] = None


class SWOTEvaluationRequest(BaseModel):
    """Input payload for Stage 13 Dynamic SWOT Agent."""
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None
    location_profile: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    opportunity_result: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    entrepreneur_readiness: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    feasibility_result: Optional[Dict[str, Any]] = None
    force_refresh: bool = False


class SWOTAnalysisResponse(BaseModel):
    """Complete Stage 13 response output contract."""
    status: str = Field("COMPLETED", description="COMPLETED | complete | FAILED | BLOCKED_NOT_FEASIBLE | fallback")
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_name: Optional[str] = None
    location: Optional[str] = None
    generation: Optional[SWOTGenerationMeta] = None
    swot: Optional[SWOTCategoryBreakdown] = None
    provenance: Optional[Dict[str, str]] = None
    strategic_summary: Optional[StrategicSummary] = None
    recommendations: List[SWOTRecommendation] = Field(default_factory=list)
    immediate_actions: List[ImmediateAction] = Field(default_factory=list)
    evidence_summary: Optional[SWOTEvidenceSummary] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    model_metadata: Optional[ModelMetadata] = None
    error_code: Optional[str] = None
    retryable: bool = False
    message: Optional[str] = None
