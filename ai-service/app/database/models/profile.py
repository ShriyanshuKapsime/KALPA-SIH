import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class StructuredBusinessProfile(TimeStampedModel):
    """
    Stage 3 Canonical Structured Business Profile:
    The single authoritative source of truth merging Stage 1 (Intake) and Stage 2 (Classification)
    for downstream consumption by the KALPA Orchestrator and specialized advisory agents.
    """
    __tablename__ = "structured_business_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # analysis_id
    session_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    schema_version = Column(String(20), default="1.0", nullable=False)
    profile_version = Column(Integer, default=1, nullable=False)
    workflow_state = Column(String(50), default="BUSINESS_PROFILE_READY", index=True, nullable=False)

    specific_business = Column(String(200), index=True, nullable=True)
    nic_code = Column(String(20), index=True, nullable=True)
    district = Column(String(100), index=True, nullable=True)
    state = Column(String(100), index=True, nullable=True)

    # Full canonical JSON document
    profile_json = Column(JSON, nullable=False)

    # Relationship
    user = relationship("User", back_populates="structured_business_profiles", foreign_keys=[user_id])
