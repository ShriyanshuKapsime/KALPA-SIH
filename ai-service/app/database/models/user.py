import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class User(TimeStampedModel):
    """
    User entity representing a rural entrepreneur, field officer, or system user.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    full_name = Column(String(150), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    preferred_language = Column(String(20), default="hi")  # e.g., 'hi', 'en', 'mr', 'ta'
    is_active = Column(Boolean, default=True)

    # Relationships
    entrepreneur_profile = relationship("EntrepreneurProfile", back_populates="user", uselist=False)
    intake_sessions = relationship("IntakeSession", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    structured_business_profiles = relationship("StructuredBusinessProfile", back_populates="user")
    orchestration_records = relationship("OrchestrationRecord", back_populates="user")
