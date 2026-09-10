import uuid
from sqlalchemy import Column, String, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class FinancialProfile(TimeStampedModel):
    """
    Financial model storing CapEx, OpEx, projected revenues, loan eligibility, and subsidy estimates.
    """
    __tablename__ = "financial_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), unique=True, nullable=False)

    total_project_cost = Column(Float, default=0.0)
    promoter_contribution = Column(Float, default=0.0)
    bank_loan_requirement = Column(Float, default=0.0)
    subsidy_amount = Column(Float, default=0.0)
    applicable_scheme_name = Column(String(100), nullable=True)  # e.g., PMEGP, PMMY Mudra

    # Financial Projections (Year 1)
    projected_annual_revenue = Column(Float, default=0.0)
    projected_operating_expenses = Column(Float, default=0.0)
    projected_net_profit = Column(Float, default=0.0)
    debt_service_coverage_ratio = Column(Float, default=0.0)  # DSCR
    break_even_percentage = Column(Float, default=0.0)

    breakdown_json = Column(JSON, default=dict)

    # Relationship
    business = relationship("BusinessProfile", back_populates="financial_profile")
