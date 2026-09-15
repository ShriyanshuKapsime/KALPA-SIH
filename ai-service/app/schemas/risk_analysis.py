from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class CategoryRiskItem(BaseModel):
    type: str = Field(..., description="MARKET | FINANCIAL | OPERATIONAL | SEASONAL | SUPPLY_CHAIN | COMPETITION | INFRASTRUCTURE")
    score: float = Field(..., ge=0.0, le=1.0, description="Deterministic risk score between 0.0 (lowest risk) and 1.0 (highest risk)")
    severity: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN")
    drivers: List[str] = Field(default_factory=list, description="Specific triggers or risk drivers identified")
    evidence: List[str] = Field(default_factory=list, description="Empirical data points or upstream stage outputs supporting the evaluation")
    impact: str = Field("", description="Real-world business impact description")
    mitigation: List[str] = Field(default_factory=list, description="Actionable MSME mitigation strategies")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence level in this category assessment")
    source_stage: str = Field("STAGE_KNOWLEDGE", description="Source stage contributing evidence (e.g. STAGE_9_FINANCIAL, STAGE_6_MARKET)")


class RiskProvenanceRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engine: str = "STAGE_11_RISK_ENGINE"
    version: str = "1.0.0"
    evaluation_type: str = "DETERMINISTIC_MULTI_VECTOR_SYNTHESIS"
    knowledge_catalog_version: str = "curated_risk_library_v1"
    critical_ceiling_applied: bool = False
    data_sources: List[str] = Field(default_factory=lambda: [
        "stage_6_market_intelligence",
        "stage_8_opportunity_evaluation",
        "stage_9_financial_engine",
        "stage_10_entrepreneur_profile",
        "curated_risk_library"
    ])


class RiskAnalysisRequest(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None
    location_profile: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[Dict[str, Any]] = None  # Stage 9 outputs (DSCR, break-even %, loan)
    market_intelligence: Optional[Dict[str, Any]] = None  # Stage 6 outputs (demand, competition, power)
    opportunity_evaluation: Optional[Dict[str, Any]] = None  # Stage 8 outputs (opportunity score)
    entrepreneur_readiness: Optional[Dict[str, Any]] = None  # Stage 10 outputs (readiness score, gaps)
    financial_profile: Optional[Dict[str, Any]] = None
    project_assumptions: Optional[Dict[str, Any]] = None


class RiskAnalysisResponse(BaseModel):
    success: bool = True
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_title: str = "Target Micro-Enterprise"
    business_node_id: Optional[str] = None
    overall_risk_score: float = Field(..., ge=0.0, le=1.0, description="Aggregated risk score between 0.0 (safe) and 1.0 (extreme risk)")
    overall_risk_severity: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    critical_risks_count: int = 0
    high_risks_count: int = 0
    category_risks: Dict[str, CategoryRiskItem] = Field(default_factory=dict)
    primary_risk_drivers: List[str] = Field(default_factory=list)
    recommended_mitigations: List[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    provenance: RiskProvenanceRecord = Field(default_factory=RiskProvenanceRecord)
