import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class NICCode(TimeStampedModel):
    """
    National Industrial Classification (NIC) reference table for Indian industry codes.
    """
    __tablename__ = "nic_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, index=True, nullable=False)  # 2-digit, 4-digit, or 5-digit
    digit_level = Column(Integer, nullable=False)  # 2, 4, or 5
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sector_category = Column(String(100), nullable=True)  # Manufacturing, Services, Agriculture


class BusinessOntology(TimeStampedModel):
    """
    Domain ontology mapping vernacular business concepts to standard enterprise classifications.
    """
    __tablename__ = "business_ontologies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vernacular_term = Column(String(150), index=True, nullable=False)
    language_code = Column(String(10), default="hi")
    standardized_concept = Column(String(150), nullable=False)
    nic_code = Column(String(10), nullable=True)
    tags = Column(JSON, default=list)


class BusinessClassification(TimeStampedModel):
    """
    Classification record linking a business profile with confidence scores to NIC & sector taxonomies.
    """
    __tablename__ = "business_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)
    nic_code_id = Column(UUID(as_uuid=True), ForeignKey("nic_codes.id"), nullable=True)

    primary_category = Column(String(100), nullable=True)  # e.g., Agro-processing, Retail, Service
    sub_category = Column(String(150), nullable=True)
    confidence_score = Column(Float, default=0.0)
    classification_metadata = Column(JSON, default=dict)

    # Relationship
    business = relationship("BusinessProfile", back_populates="classification")


class BusinessProfile(TimeStampedModel):
    """
    Core business entity capturing the proposed or existing rural venture.
    """
    __tablename__ = "business_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrepreneur_id = Column(UUID(as_uuid=True), ForeignKey("entrepreneur_profiles.id"), nullable=False)

    business_name = Column(String(200), nullable=True)
    venture_description = Column(Text, nullable=True)
    target_scale = Column(String(50), default="micro")  # nano, micro, small
    business_model = Column(String(50), nullable=True)  # B2C, B2B, D2C, Hybrid
    proposed_investment = Column(Float, default=0.0)

    # Location of proposed enterprise
    location_pincode = Column(String(10), nullable=True)
    location_district = Column(String(100), nullable=True)
    location_state = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Relationships
    entrepreneur = relationship("EntrepreneurProfile", back_populates="business_profiles")
    classification = relationship("BusinessClassification", back_populates="business", uselist=False)
    market_intelligence = relationship("MarketIntelligenceProfile", back_populates="business", uselist=False)
    financial_profile = relationship("FinancialProfile", back_populates="business", uselist=False)
    feasibility_result = relationship("FeasibilityResult", back_populates="business", uselist=False)
    opportunity_evaluation = relationship("OpportunityEvaluation", back_populates="business", uselist=False)
    reports = relationship("GeneratedReport", back_populates="business")
