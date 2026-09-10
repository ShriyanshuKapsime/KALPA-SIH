import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class EntrepreneurProfile(TimeStampedModel):
    """
    Structured profile of a rural entrepreneur including demographic, financial risk, and skill attributes.
    """
    __tablename__ = "entrepreneur_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    age = Column(Integer, nullable=True)
    gender = Column(String(30), nullable=True)
    education_level = Column(String(100), nullable=True)
    caste_category = Column(String(50), nullable=True)  # General, OBC, SC, ST (for scheme matching)
    
    # Location details
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    sub_district_block = Column(String(100), nullable=True)
    village_town = Column(String(150), nullable=True)
    pincode = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Capability & Capacity
    prior_experience_years = Column(Float, default=0.0)
    primary_skills = Column(JSON, default=list)  # List of skill keywords
    risk_appetite = Column(String(50), default="moderate")  # low, moderate, high
    available_own_capital = Column(Float, default=0.0)
    has_land_or_premise = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="entrepreneur_profile")
    business_profiles = relationship("BusinessProfile", back_populates="entrepreneur")
