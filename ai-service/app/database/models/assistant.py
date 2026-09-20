"""
SQLAlchemy Models for Stage 15: Personal AI Business Assistant.
Persists conversation messages, structured business memory, and conversation memory.
"""
import uuid
import datetime
from sqlalchemy import Column, String, Float, Integer, Text, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import TimeStampedModel


class AssistantConversation(TimeStampedModel):
    """
    Persisted assistant conversation message record.
    Each row = one user message + assistant response pair.
    """
    __tablename__ = "assistant_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    business_id = Column(UUID(as_uuid=True), nullable=True)

    # Message content
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=True)
    intent = Column(String(100), nullable=True)
    language = Column(String(20), default="en")
    confidence = Column(Float, default=0.0)

    # Grounding
    grounded_sources = Column(JSON, default=list)
    suggested_actions = Column(JSON, default=list)

    # Ordering
    message_index = Column(Integer, default=0)


class AssistantMemory(TimeStampedModel):
    """
    Structured business memory and conversation memory for the assistant.
    Scoped to user/session/business/analysis — never mixed between businesses.
    """
    __tablename__ = "assistant_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # A. Canonical Business Memory
    business_memory = Column(JSON, default=dict)
    # {
    #   "business_name": "...", "business_type": "...", "location": "...",
    #   "capital": 0, "objectives": [], "language": "...",
    #   "selected_scheme": null, "selected_loan": null,
    #   "dpr_status": "NOT_GENERATED", "launch_status": "PRE_LAUNCH"
    # }

    # B. Conversation Memory (structured summaries of past conversations)
    conversation_memory = Column(JSON, default=dict)
    # {
    #   "questions_answered": [], "user_concerns": [],
    #   "user_decisions": [], "selected_actions": [],
    #   "clarifications": [], "preferences": {}
    # }

    # Workflow state snapshot
    business_status = Column(String(30), default="PRE_LAUNCH")  # PRE_LAUNCH, LAUNCHED
