import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import TimeStampedModel


class OrchestrationRecord(TimeStampedModel):
    """
    Stage 4 Orchestrator Execution Record:
    Persists the full LangGraph state, dynamic execution plan, agent execution results,
    decision history trace, and final synthesized canonical output.
    """
    __tablename__ = "orchestration_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # analysis_id
    session_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    schema_version = Column(String(20), default="1.0", nullable=False)
    workflow_status = Column(String(64), default="ORCHESTRATION_COMPLETE", index=True, nullable=False)
    current_node = Column(String(64), nullable=True)

    # Structured LangGraph Execution Data
    execution_plan = Column(JSON, default=list, nullable=False)
    completed_agents = Column(JSON, default=list, nullable=False)
    pending_agents = Column(JSON, default=list, nullable=False)
    agent_results = Column(JSON, default=dict, nullable=False)
    knowledge_context = Column(JSON, default=dict, nullable=False)
    decision_history = Column(JSON, default=list, nullable=False)
    routing_metadata = Column(JSON, default=dict, nullable=False)
    llm_usage = Column(JSON, default=dict, nullable=False)
    errors = Column(JSON, default=list, nullable=False)

    # Final synthesized Stage 4 response document
    orchestration_output = Column(JSON, nullable=False)

    # Relationships
    user = relationship("User", back_populates="orchestration_records", foreign_keys=[user_id])
