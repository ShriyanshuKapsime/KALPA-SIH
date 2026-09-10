import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class IntakeSession(TimeStampedModel):
    """
    Intake session capturing user input, language metadata, deterministic extraction, and structured profile JSON.
    """
    __tablename__ = "intake_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    input_type = Column(String(50), default="text")  # 'voice' or 'text'
    original_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    language_code = Column(String(20), default="en")
    language_name = Column(String(50), default="English")

    structured_profile = Column(JSON, default=dict)
    pipeline_status = Column(String(50), default="completed")  # completed, processing, failed

    # Relationships
    user = relationship("User", back_populates="intake_sessions")


class Conversation(TimeStampedModel):
    """
    Conversational transcript between user and the KALPA interactive advisory agent.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=True)

    role = Column(String(30), nullable=False)  # user, assistant, system, tool
    message_content = Column(Text, nullable=False)
    language_code = Column(String(10), default="hi")
    metadata_payload = Column(JSON, default=dict)

    # Relationship
    user = relationship("User", back_populates="conversations")
