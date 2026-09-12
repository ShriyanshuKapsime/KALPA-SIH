from typing import Optional, Dict, Any, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime


class ExecutionPlanItem(BaseModel):
    step: int
    agent: str
    purpose: str
    priority: str = "HIGH"  # HIGH | MEDIUM | LOW
    status: str = "pending"  # pending | ready | completed | failed | skipped
    dependencies: List[str] = Field(default_factory=list)


class DecisionTraceItem(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    node: str
    observation: str
    decision: str
    reason: str
    decision_source: str = "deterministic"  # deterministic | hybrid | llm | fallback
    confidence: float = 1.0
    next_action: Optional[Dict[str, Any]] = None


class LLMUsageInfo(BaseModel):
    calls: int = 0
    used: bool = False
    reasons: List[str] = Field(default_factory=list)


class RoutingMetadata(BaseModel):
    decision_source: str = "deterministic"
    deterministic_confidence: float = 1.0
    factors: Dict[str, float] = Field(default_factory=dict)
    llm_used: bool = False
    llm_reason: Optional[str] = None
    explanation: str = ""


class AgentExecutionSummary(BaseModel):
    completed: List[str] = Field(default_factory=list)
    pending: List[str] = Field(default_factory=list)
    failed: List[str] = Field(default_factory=list)
    total_planned: int = 0


# TypedDict State for LangGraph Engine
class KALPAOrchestratorState(TypedDict, total=False):
    analysis_id: str
    session_id: str
    user_id: Optional[str]

    # Canonical Stage 3 Profile
    business_profile: Dict[str, Any]

    workflow_status: str  # ANALYZING | PLANNING | EXECUTING | ORCHESTRATION_COMPLETE | CLARIFICATION_REQUIRED | FAILED
    current_node: str

    execution_plan: List[Dict[str, Any]]
    pending_agents: List[str]
    completed_agents: List[str]
    current_agent: Optional[str]

    agent_results: Dict[str, Any]
    knowledge_context: Dict[str, Any]

    decision_history: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    retry_counts: Dict[str, int]
    routing_metadata: Dict[str, Any]

    llm_usage: Dict[str, Any]
    final_decision: Dict[str, Any]
    next_action: Dict[str, Any]


class StartOrchestratorRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Active session UUID")
    analysis_id: Optional[str] = Field(default=None, description="Direct Stage 3 profile UUID")
    business_profile: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw Stage 3 profile JSON override")
    force_llm: bool = Field(default=False, description="Flag for testing/evaluating LLM escalation path")


class CanonicalWorkflowState(BaseModel):
    session_id: str
    analysis_id: str
    business_id: Optional[str] = None
    current_stage: int = 4
    workflow_status: str = "ORCHESTRATION_COMPLETE"
    completed_stages: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 8, 9])
    available_stages: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 8, 9])
    locked_stages: List[int] = Field(default_factory=lambda: [10, 11, 12, 13, 14, 15])
    active_agent: Optional[str] = None
    next_stage: Optional[int] = 5
    stage_name: str = "KALPA_MANAGER_ORCHESTRATOR"
    journey_status: Dict[str, Any] = Field(default_factory=lambda: {
        "understand": "COMPLETED",
        "discover": "ACTIVE",
        "validate": "PENDING",
        "finance": "PENDING",
        "prepare": "LOCKED",
        "grow": "LOCKED"
    })
    engine_outputs: Dict[str, Any] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorResponse(BaseModel):
    success: bool = True
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str
    business_id: Optional[str] = None
    workflow_status: str = "ORCHESTRATION_COMPLETE"
    current_stage: int = 4
    completed_stages: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    active_agent: Optional[str] = None
    next_stage: Optional[int] = 5
    orchestration_status: str = "ORCHESTRATION_COMPLETE"
    workflow: CanonicalWorkflowState
    business_context: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    agent_execution_summary: AgentExecutionSummary
    knowledge_context: Dict[str, Any] = Field(default_factory=dict)
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    routing_summary: RoutingMetadata
    decision_history: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: Dict[str, Any] = Field(default_factory=dict)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
