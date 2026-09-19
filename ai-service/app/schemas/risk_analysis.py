from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone


class CategoryRiskItem(BaseModel):
    category: str = Field(..., description="FINANCIAL | MARKET | OPERATIONAL | SEASONAL | SUPPLY_CHAIN | COMPETITION | INFRASTRUCTURE")
    type: Optional[str] = Field(None, description="Compatibility alias for category")
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Deterministic risk score between 0.0 (lowest risk) and 1.0 (highest risk) or None if DATA_GAP")
    level: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN")
    severity: str = Field("UNKNOWN", description="Compatibility alias for level")
    status: Optional[str] = Field(None, description="STRONG | ADEQUATE | CAUTION | CRITICAL | DATA_GAP | UNKNOWN")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence level in this category assessment")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Exact upstream stage input values consumed")
    benchmarks: List[Dict[str, Any]] = Field(default_factory=list, description="Benchmark reference thresholds applied")
    formula: str = Field("", description="Calculation formula or logic applied")
    drivers: List[str] = Field(default_factory=list, description="Specific triggers or risk drivers identified")
    mitigations: List[str] = Field(default_factory=list, description="Actionable MSME mitigation strategies")
    mitigation: List[str] = Field(default_factory=list, description="Compatibility alias for mitigations")
    evidence: List[str] = Field(default_factory=list, description="Empirical data points or upstream stage outputs supporting the evaluation")
    evidence_refs: List[str] = Field(default_factory=list, description="Upstream field references (e.g. stage9.debt_service.dscr)")
    impact: str = Field("", description="Real-world business impact description")
    source_stage: str = Field("STAGE_KNOWLEDGE", description="Source stage contributing evidence (e.g. STAGE_9_FINANCIAL, STAGE_6_MARKET)")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # category / type sync
            if "category" not in data and "type" in data:
                data["category"] = data["type"]
            elif "type" not in data and "category" in data:
                data["type"] = data["category"]

            # level / severity / status sync
            if "level" not in data and "severity" in data:
                data["level"] = data["severity"]
            elif "severity" not in data and "level" in data:
                data["severity"] = data["level"]
            if "status" not in data and "level" in data:
                data["status"] = data["level"]

            # mitigations / mitigation sync
            if "mitigations" not in data and "mitigation" in data:
                data["mitigations"] = data["mitigation"]
            elif "mitigation" not in data and "mitigations" in data:
                data["mitigation"] = data["mitigations"]
        return data


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
    overall_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Aggregated risk score between 0.0 (safe) and 1.0 (extreme risk)")
    overall_risk_severity: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN | DATA_GAP")
    overall_score: Optional[float] = None
    overall_level: Optional[str] = None
    critical_risks_count: int = 0
    high_risks_count: int = 0
    category_scores: Dict[str, Optional[float]] = Field(default_factory=dict)
    weights: Dict[str, float] = Field(default_factory=dict)
    weighted_contributions: Dict[str, float] = Field(default_factory=dict)
    category_risks: Dict[str, CategoryRiskItem] = Field(default_factory=dict)
    calculation_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    primary_risk_drivers: List[str] = Field(default_factory=list)
    recommended_mitigations: List[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    provenance: RiskProvenanceRecord = Field(default_factory=RiskProvenanceRecord)

    @model_validator(mode="before")
    @classmethod
    def sync_risk_response_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "overall_score" not in data and "overall_risk_score" in data:
                data["overall_score"] = data["overall_risk_score"]
            elif "overall_risk_score" not in data and "overall_score" in data:
                data["overall_risk_score"] = data["overall_score"]

            if "overall_level" not in data and "overall_risk_severity" in data:
                data["overall_level"] = data["overall_risk_severity"]
            elif "overall_risk_severity" not in data and "overall_level" in data:
                data["overall_risk_severity"] = data["overall_level"]
        return data
