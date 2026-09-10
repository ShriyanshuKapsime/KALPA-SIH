import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class GeneratedReport(TimeStampedModel):
    """
    Detailed Project Report (DPR) or Advisory Summary generated for banks and government schemes.
    """
    __tablename__ = "generated_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)

    report_type = Column(String(50), default="dpr")  # dpr, executive_summary, swot_pivot
    file_format = Column(String(20), default="pdf")  # pdf, docx, json
    file_path = Column(String(500), nullable=True)
    report_title = Column(String(255), nullable=True)
    report_summary = Column(Text, nullable=True)
    report_payload = Column(JSON, default=dict)

    # Relationship
    business = relationship("BusinessProfile", back_populates="reports")
