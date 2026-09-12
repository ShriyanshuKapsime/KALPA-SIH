import uuid
from sqlalchemy import Column, String, Float, ForeignKey, JSON, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class BenchmarkReference(TimeStampedModel):
    """
    Reference benchmark values (e.g. NABARD unit costs, average CapEx, OpEx margin ratios).
    """
    __tablename__ = "benchmark_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benchmark_code = Column(String(50), unique=True, index=True, nullable=False)
    sector_name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    recommended_unit_cost = Column(Float, nullable=True)
    expected_margin_percentage = Column(Float, nullable=True)
    working_capital_ratio = Column(Float, nullable=True)
    benchmark_source = Column(String(100), default="NABARD Unit Cost 2024-25")
    attributes_json = Column(JSON, default=dict)


class MarketIntelligenceProfile(TimeStampedModel):
    """
    Geospatial and hyper-local market intelligence collected for a business profile.
    """
    __tablename__ = "market_intelligence_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), unique=True, nullable=False)

    analysis_radius_km = Column(Float, default=5.0)
    competitor_count = Column(Integer, default=0)
    market_saturation_index = Column(Float, default=0.0)  # 0.0 to 1.0
    estimated_catchment_population = Column(Integer, default=0)
    estimated_monthly_demand = Column(Float, default=0.0)
    
    # Infrastructure accessibility
    nearest_highway_km = Column(Float, nullable=True)
    nearest_bank_branch_km = Column(Float, nullable=True)
    nearest_mandi_or_market_km = Column(Float, nullable=True)
    
    raw_spatial_data = Column(JSON, default=dict)

    # Relationship
    business = relationship("BusinessProfile", back_populates="market_intelligence")


class OpportunityEvaluation(TimeStampedModel):
    """
    Opportunity rating across hyper-local growth vectors and unmet demand gaps.
    """
    __tablename__ = "opportunity_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), unique=True, nullable=False)

    opportunity_score = Column(Float, default=0.0)  # 0 to 100
    demand_supply_gap = Column(String(50), default="moderate")  # high, moderate, saturated
    recommended_scale = Column(String(50), default="micro")
    growth_potential_rating = Column(String(20), default="medium")  # high, medium, low
    key_drivers = Column(JSON, default=list)

    # Relationship
    business = relationship("BusinessProfile", back_populates="opportunity_evaluation")


class MarketEvidenceRecord(TimeStampedModel):
    """
    Stage 5 Market Evidence Record:
    Persists the full Stage 5 raw evidence collected, location resolution context,
    collection plan, explainable quality breakdown, evidence gaps, execution trace, and provenance.
    """
    __tablename__ = "market_evidence_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # analysis_id
    session_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    schema_version = Column(String(20), default="1.0", nullable=False)
    workflow_status = Column(String(64), default="MARKET_EVIDENCE_COLLECTED", index=True, nullable=False)
    geographic_precision = Column(String(32), default="district", nullable=False)
    overall_quality_score = Column(Float, default=0.0, nullable=False)

    # Structured Components
    location_context = Column(JSON, default=dict, nullable=False)
    collection_plan = Column(JSON, default=dict, nullable=False)
    market_evidence = Column(JSON, default=dict, nullable=False)
    evidence_quality = Column(JSON, default=dict, nullable=False)
    evidence_gaps = Column(JSON, default=list, nullable=False)
    execution_metadata = Column(JSON, default=dict, nullable=False)
    provenance = Column(JSON, default=dict, nullable=False)

    # Full canonical JSON document
    full_profile = Column(JSON, nullable=False)

