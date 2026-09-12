import uuid
from sqlalchemy import Column, String, Integer, Float, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import TimeStampedModel


class KnowledgeDataSource(TimeStampedModel):
    """
    Catalog of all official datasets and registries ingested into KALPA Knowledge Hub.
    """
    __tablename__ = "knowledge_data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(String(100), unique=True, index=True, nullable=False)
    dataset_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    official_source = Column(String(255), nullable=False)
    ministry_or_nodal_agency = Column(String(255), nullable=False)
    file_format = Column(String(50), default="JSON")
    ingestion_status = Column(String(50), default="AVAILABLE", index=True)
    records_count = Column(Integer, default=0)
    coverage_domain = Column(String(100), nullable=False)
    last_sync_date = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)


class GovernmentSchemeModel(TimeStampedModel):
    """
    Official government schemes and baseline loan rules with explicit provenance.
    """
    __tablename__ = "knowledge_government_schemes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(String(100), unique=True, index=True, nullable=False)
    scheme_name = Column(String(255), nullable=False)
    nodal_agency = Column(String(255), nullable=False)
    ministry_or_body = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False)
    scheme_tier = Column(String(100), nullable=False)
    validity_status = Column(String(50), default="ACTIVE", index=True)
    application_mode = Column(String(100), default="ONLINE_PORTAL")

    provenance_json = Column(JSON, default=dict)
    eligibility_criteria = Column(JSON, default=dict)
    financial_terms = Column(JSON, default=dict)
    applicable_sectors = Column(JSON, default=list)
    documentation_required = Column(JSON, default=list)


class FinancialBenchmarkModel(TimeStampedModel):
    """
    Financial benchmarks: capex, working capital, gross/net margins, payback period.
    """
    __tablename__ = "knowledge_financial_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_node_id = Column(String(100), unique=True, index=True, nullable=False)
    business_title = Column(String(255), nullable=False)
    nic_code = Column(String(20), nullable=True, index=True)
    currency = Column(String(10), default="INR")

    provenance_json = Column(JSON, default=dict)
    capex_json = Column(JSON, default=dict)
    working_capital_json = Column(JSON, default=dict)
    margins_json = Column(JSON, default=dict)
    cost_structure_json = Column(JSON, default=dict)
    timelines_json = Column(JSON, default=dict)
    unit_economics_json = Column(JSON, default=dict)


class MarketBenchmarkModel(TimeStampedModel):
    """
    Market benchmarks: catchment radius, competition saturation, seasonality multipliers.
    """
    __tablename__ = "knowledge_market_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_node_id = Column(String(100), unique=True, index=True, nullable=False)
    business_title = Column(String(255), nullable=False)

    catchment_json = Column(JSON, default=dict)
    competition_json = Column(JSON, default=dict)
    seasonality_json = Column(JSON, default=dict)
    seasonality_notes = Column(Text, nullable=True)
    demand_drivers = Column(JSON, default=list)
    target_customer_segments = Column(JSON, default=list)
    provenance_json = Column(JSON, default=dict)


class BusinessRequirementModel(TimeStampedModel):
    """
    Business technical domain requirements: equipment, space, power, manpower, licenses.
    """
    __tablename__ = "knowledge_business_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_node_id = Column(String(100), unique=True, index=True, nullable=False)
    business_title = Column(String(255), nullable=False)

    space_and_infrastructure = Column(JSON, default=dict)
    power_and_utilities = Column(JSON, default=dict)
    core_machinery = Column(JSON, default=list)
    skills_and_manpower = Column(JSON, default=dict)
    supply_chain = Column(JSON, default=dict)
    compliance_and_licensing = Column(JSON, default=list)


class RiskLibraryModel(TimeStampedModel):
    """
    Structured risk library catalog categorized with triggers, severity, and mitigations.
    """
    __tablename__ = "knowledge_risk_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(String(100), unique=True, index=True, nullable=False)
    risk_name = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False)  # OPERATIONAL | FINANCIAL | REGULATORY | MARKET | CLIMATE
    severity = Column(String(50), index=True, nullable=False)    # LOW | MEDIUM | HIGH | CRITICAL
    probability = Column(String(50), default="MEDIUM")

    applicable_business_nodes = Column(JSON, default=list)
    trigger_events = Column(JSON, default=list)
    impact_description = Column(Text, nullable=False)
    mitigation_strategies = Column(JSON, default=list)
    monitoring_indicators = Column(JSON, default=list)


class InstitutionalDocumentModel(TimeStampedModel):
    """
    Institutional knowledge documents from NABARD, RBI, MSME, SIDBI, FSSAI with extraction tracking.
    """
    __tablename__ = "knowledge_institutional_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    publication_year = Column(Integer, default=2024)
    category = Column(String(100), nullable=False)
    document_url = Column(String(500), nullable=False)
    file_format = Column(String(20), default="PDF")
    ingestion_status = Column(String(50), default="REGISTERED", index=True)
    extracted_at = Column(String(50), nullable=True)
    summary = Column(Text, nullable=False)

    key_insights = Column(JSON, default=dict)
    applicable_business_nodes = Column(JSON, default=list)


class DynamicDataRequirementModel(TimeStampedModel):
    """
    Dynamic data requirement layer defining external parameters needed by future engines.
    """
    __tablename__ = "knowledge_dynamic_data_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(String(100), unique=True, index=True, nullable=False)
    requirement_name = Column(String(255), nullable=False)
    domain = Column(String(100), index=True, nullable=False)
    refresh_frequency = Column(String(50), default="MONTHLY")
    ingestion_method = Column(String(100), default="API_PULL")
    priority = Column(String(50), default="HIGH")
    fallback_strategy = Column(String(255), nullable=False)

    target_parameters = Column(JSON, default=list)
    candidate_sources = Column(JSON, default=list)
    consuming_engines = Column(JSON, default=list)
