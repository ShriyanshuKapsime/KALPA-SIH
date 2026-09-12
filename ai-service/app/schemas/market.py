"""
Stage 5 Market Intelligence Agent Schemas.
Authoritative schemas for autonomous market evidence collection, location resolution,
canonical business context, deterministic execution context, tool results,
explainable evidence quality scoring, provenance, and API communication.
"""
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# 1. Canonical Business Context & Data Status
# -----------------------------------------------------------------------------

class EvidenceDataStatus(str, Enum):
    LIVE_RETRIEVED = "LIVE_RETRIEVED"
    OFFICIAL_STATIC_DATA = "OFFICIAL_STATIC_DATA"
    CACHED_VERIFIED_DATA = "CACHED_VERIFIED_DATA"
    PROXY = "PROXY"
    ESTIMATED = "ESTIMATED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


class CanonicalBusinessContext(BaseModel):
    """
    Mandatory normalized business context for Stage 5 execution.
    Isolates business identity, preventing cross-business data contamination.
    """
    business_id: str
    business_name: str
    business_category: str
    analysis_id: str
    session_id: str
    profile_version: str = "1.0"
    classification_source: str = "STAGE_4.5_CANONICAL"
    knowledge_profile_version: str = "2026.1"
    specific_business: Optional[str] = None
    normalized_concept: Optional[str] = None
    sector: Optional[str] = None
    nic_code: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# 2. Location Resolution & Context Schemas
# -----------------------------------------------------------------------------

class LocationCoordinates(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


class AdministrativeHierarchy(BaseModel):
    village: Optional[str] = None
    gram_panchayat: Optional[str] = None
    block: Optional[str] = None
    tehsil_taluk: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None


class LocationConflictInfo(BaseModel):
    has_conflict: bool = False
    location_conflict: bool = False
    user_location_text: Optional[str] = None
    gps_resolved_text: Optional[str] = None
    text_location: Optional[Dict[str, Any]] = None
    gps_location: Optional[Dict[str, Any]] = None
    selected_location: Optional[Dict[str, Any]] = None
    selection_reason: Optional[str] = None
    distance_km: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None


class LocationContext(BaseModel):
    resolved_location: AdministrativeHierarchy = Field(default_factory=AdministrativeHierarchy)
    coordinates: LocationCoordinates = Field(default_factory=LocationCoordinates)
    geographic_precision: str = "district"  # "village" | "block" | "district" | "state" | "national"
    target_geographic_precision: str = "village"
    data_geographic_precision: str = "district"
    resolution_confidence: float = 0.0
    resolution_method: str = "deterministic_catalog"  # "gps_reverse_geocoding" | "forward_geocoding" | "district_fallback"
    conflict: LocationConflictInfo = Field(default_factory=LocationConflictInfo)


# -----------------------------------------------------------------------------
# 3. Canonical Execution Context
# -----------------------------------------------------------------------------

class MarketExecutionContext(BaseModel):
    """
    Immutable single source of truth for all Stage 5 tool invocations.
    """
    analysis_id: str
    session_id: str
    business: CanonicalBusinessContext
    location: LocationContext
    requirements: List[str] = Field(default_factory=list)
    knowledge_context: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = "live"  # "live" | "cached" | "static" | "proxy"
    force_refresh: bool = False


# -----------------------------------------------------------------------------
# 4. Collection Plan Schemas
# -----------------------------------------------------------------------------

class CollectionPlan(BaseModel):
    planner: str = "deterministic"  # "llm" | "deterministic" | "fallback"
    business_id: str = ""
    requirements: List[str] = Field(default_factory=list)
    selected_tools: List[str] = Field(default_factory=list)
    fallback_used: bool = False
    reasoning: Optional[str] = None
    requirements_source: str = "Stage 4.5 Domain Knowledge & Benchmark Ontology"


# -----------------------------------------------------------------------------
# 5. Individual Evidence Item Schemas with Provenance & Precision Truthfulness
# -----------------------------------------------------------------------------

class DemographicEvidenceItem(BaseModel):
    metric: str
    value: Any
    unit: str = "persons"
    geography: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    target_geographic_precision: str = "village"
    data_geographic_precision: str = "district"
    data_status: str = "OFFICIAL_STATIC_DATA"  # EvidenceDataStatus
    source: Dict[str, Any] = Field(default_factory=dict)
    reference_period: str = "Census 2011 / LGD 2024"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    proxy: bool = False
    proxy_reason: Optional[str] = None
    retrieval_method: str = "CURATED_DATASET"


class CompetitorEvidenceItem(BaseModel):
    competitor_type: str = "direct"  # "direct" | "adjacent" | "substitute"
    business_name: str
    category: str
    location: Dict[str, Any] = Field(default_factory=dict)
    distance_km: Optional[float] = None
    data_status: str = "OFFICIAL_STATIC_DATA"
    source: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.85
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"


class CompetitorEvidenceContainer(BaseModel):
    status: str = "success"  # "success" | "partial" | "failed" | "unavailable"
    error: Optional[str] = None
    direct: List[CompetitorEvidenceItem] = Field(default_factory=list)
    adjacent: List[CompetitorEvidenceItem] = Field(default_factory=list)
    substitutes: List[CompetitorEvidenceItem] = Field(default_factory=list)
    total_found: int = 0


class DemandIndicatorItem(BaseModel):
    indicator_name: str
    category: str = "general"
    value: Any
    unit: str = "index"
    business_relevance: str = ""
    data_status: str = "OFFICIAL_STATIC_DATA"
    geography: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    data_geographic_precision: str = "district"
    source: Dict[str, Any] = Field(default_factory=dict)
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"


class SupplyAccessItem(BaseModel):
    hub_name: str
    hub_type: str  # "wholesale_market" | "mandi" | "raw_material_cluster" | "cooperative"
    distance_km: Optional[float] = None
    commodities_available: List[str] = Field(default_factory=list)
    accessibility_rating: str = "moderate"  # "high" | "moderate" | "low"
    data_status: str = "OFFICIAL_STATIC_DATA"
    source: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    data_geographic_precision: str = "district"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"


class InfrastructureItem(BaseModel):
    infrastructure_type: str  # "road" | "commercial_hub" | "electricity" | "transport" | "banking" | "warehousing"
    name: str
    distance_km: Optional[float] = None
    status: str = "available"  # "available" | "partial" | "unavailable"
    reliability_hours_daily: Optional[float] = None
    data_status: str = "OFFICIAL_STATIC_DATA"
    source: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    data_geographic_precision: str = "district"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"


class EconomicIndicatorItem(BaseModel):
    indicator_type: str  # "per_capita_income" | "rural_wage_rate" | "poverty_headcount" | "banking_density"
    value: Any
    unit: str = "INR"
    proxy: bool = False
    proxy_reason: Optional[str] = None
    data_status: str = "PROXY"
    geographic_precision: str = "district"
    data_geographic_precision: str = "district"
    source: Dict[str, Any] = Field(default_factory=dict)
    reference_period: str = "2023-24"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"


class SeasonalityEvidenceItem(BaseModel):
    factor_name: str
    peak_months: List[str] = Field(default_factory=list)
    lean_months: List[str] = Field(default_factory=list)
    seasonal_notes: str = ""
    monthly_multipliers: Dict[str, float] = Field(default_factory=dict)
    data_status: str = "OFFICIAL_STATIC_DATA"
    source: Dict[str, Any] = Field(default_factory=dict)
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "STATIC_KNOWLEDGE"


class DemandPredictionAdapterResult(BaseModel):
    available: bool = False
    status: str = "model_not_connected"  # "ready" | "model_not_connected" | "error"
    data_status: str = "UNAVAILABLE"
    prediction: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = "Demand prediction ML model is currently offline or not connected."
    recommended_action: Optional[str] = "connect_demand_prediction_model"


# -----------------------------------------------------------------------------
# 6. Evidence Aggregate Container
# -----------------------------------------------------------------------------

class MarketEvidenceAggregate(BaseModel):
    demographics: List[DemographicEvidenceItem] = Field(default_factory=list)
    competitors: CompetitorEvidenceContainer = Field(default_factory=CompetitorEvidenceContainer)
    demand_indicators: List[DemandIndicatorItem] = Field(default_factory=list)
    supply_access: List[SupplyAccessItem] = Field(default_factory=list)
    infrastructure: List[InfrastructureItem] = Field(default_factory=list)
    economic_indicators: List[EconomicIndicatorItem] = Field(default_factory=list)
    seasonality_evidence: List[SeasonalityEvidenceItem] = Field(default_factory=list)
    demand_prediction: DemandPredictionAdapterResult = Field(default_factory=DemandPredictionAdapterResult)


# -----------------------------------------------------------------------------
# 7. Quality, Gaps, Execution & Provenance
# -----------------------------------------------------------------------------

class EvidenceQualityBreakdown(BaseModel):
    completeness: float = 0.0          # 25% weight
    source_quality: float = 0.0        # 20% weight
    geographic_relevance: float = 0.0  # 15% weight
    freshness: float = 0.0             # 10% weight
    validation: float = 0.0            # 10% weight
    semantic_relevance: float = 0.0    # 10% weight
    tool_success: float = 0.0          # 10% weight


class EvidenceQuality(BaseModel):
    completeness: float = 0.0
    source_quality: float = 0.0
    geographic_relevance: float = 0.0
    freshness: float = 0.0
    semantic_relevance_score: float = 1.0
    tool_success_score: float = 1.0
    overall_quality: float = 0.0
    confidence_level: str = "high"  # "high" | "moderate" | "low" | "untrustworthy"
    breakdown: EvidenceQualityBreakdown = Field(default_factory=EvidenceQualityBreakdown)
    missing_requirements: List[str] = Field(default_factory=list)
    quality_notes: List[str] = Field(default_factory=list)


class EvidenceGapItem(BaseModel):
    requirement: str
    reason: str
    severity: str = "warning"  # "critical" | "warning" | "info"
    recommended_action: str


class ExecutionMetadata(BaseModel):
    tools_called: List[str] = Field(default_factory=list)
    successful_tools: List[str] = Field(default_factory=list)
    failed_tools: List[str] = Field(default_factory=list)
    retried_tools: List[str] = Field(default_factory=list)
    cached_tools: List[str] = Field(default_factory=list)
    llm_used: bool = False
    llm_fallback_used: bool = False
    execution_time_seconds: float = 0.0
    execution_state: str = "DETERMINISTIC_ONLY"  # LLM_SUCCESS | LLM_HTTP_SUCCESS_PARSE_FAILURE | LLM_SCHEMA_FAILURE | LLM_FALLBACK | DETERMINISTIC_ONLY
    sarvam_request_success: Optional[bool] = None
    sarvam_http_status: Optional[int] = None
    sarvam_response_received: Optional[bool] = None
    sarvam_response_shape: Optional[str] = None
    sarvam_content_extracted: Optional[bool] = None
    sarvam_response_parsed: Optional[bool] = None
    sarvam_schema_valid: Optional[bool] = None
    sarvam_response_validation_success: Optional[bool] = None
    sarvam_fallback_triggered: Optional[bool] = None
    sarvam_fallback_reason: Optional[str] = None


class ProvenanceItem(BaseModel):
    source_id: str
    organization: str
    source_type: str = "OFFICIAL_DATASET"
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    dataset_name: Optional[str] = None
    url: Optional[str] = None
    retrieval_method: str = "CURATED_DATASET"
    query_parameters: Dict[str, Any] = Field(default_factory=dict)
    data_status: str = "OFFICIAL_STATIC_DATA"


class ProvenanceContainer(BaseModel):
    sources: List[ProvenanceItem] = Field(default_factory=list)
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class WorkflowSection(BaseModel):
    stage: int = 5
    state: str = "MARKET_EVIDENCE_COLLECTED"
    status: str = "complete"  # "complete" | "partial" | "failed"


# -----------------------------------------------------------------------------
# 8. Canonical Stage 5 Output: MarketEvidenceProfile
# -----------------------------------------------------------------------------

class MarketEvidenceProfile(BaseModel):
    """
    Stage 5 Canonical Structured Market Evidence Document.
    Authoritative container of raw, validated, and provenance-tracked market evidence.
    """
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str

    workflow: WorkflowSection = Field(default_factory=WorkflowSection)
    business_context: CanonicalBusinessContext = Field(
        default_factory=lambda: CanonicalBusinessContext(
            business_id="uncurated",
            business_name="Uncurated Enterprise",
            business_category="General",
            analysis_id="",
            session_id=""
        )
    )
    location_context: LocationContext = Field(default_factory=LocationContext)
    collection_plan: CollectionPlan = Field(default_factory=CollectionPlan)
    market_evidence: MarketEvidenceAggregate = Field(default_factory=MarketEvidenceAggregate)
    evidence_quality: EvidenceQuality = Field(default_factory=EvidenceQuality)
    evidence_gaps: List[EvidenceGapItem] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    provenance: ProvenanceContainer = Field(default_factory=ProvenanceContainer)

    model_config = {
        "populate_by_name": True
    }


# -----------------------------------------------------------------------------
# 9. API Request & Response Schemas
# -----------------------------------------------------------------------------

class CollectMarketEvidenceRequest(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_id: Optional[str] = None
    business_profile: Optional[Dict[str, Any]] = None
    force_llm: bool = False
    force_refresh: bool = False


class CollectMarketEvidenceResponse(BaseModel):
    success: bool = True
    analysis_id: str
    session_id: str
    status: str
    evidence_profile: MarketEvidenceProfile


class ToolHealthItem(BaseModel):
    tool: str = ""
    tool_name: str = ""
    status: str  # "available" | "degraded" | "unavailable" | "model_not_connected" | "configuration_missing"
    latency_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class ToolHealthReport(BaseModel):
    status: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    total_tools: int = 10
    healthy_tools: int = 9
    tools: List[ToolHealthItem] = Field(default_factory=list)


class RetryExecutionRequest(BaseModel):
    failed_tools_only: bool = True
    force_refresh: bool = True


# Legacy spatial models retained for backwards compatibility
class SpatialAnalysisRequest(BaseModel):
    business_id: str
    latitude: float
    longitude: float
    radius_km: float = 5.0
    sector_category: str


class MarketIntelligenceResponse(BaseModel):
    business_id: str
    competitor_count: int
    saturation_level: str
    estimated_monthly_demand: float
    nearest_infrastructure: Dict[str, Optional[float]] = Field(default_factory=dict)
