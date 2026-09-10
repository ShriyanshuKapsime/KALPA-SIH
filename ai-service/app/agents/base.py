"""
Base Agent Interface and State Schema for LangGraph multi-agent orchestration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Standard state container passed across LangGraph nodes.
    """
    session_id: str
    user_id: Optional[str] = None
    business_id: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    current_node: str = "init"
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class BaseKalpaAgent(ABC):
    """
    Abstract base class for all KALPA autonomous and advisory agents.
    """
    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description

    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Execute agent step. To be implemented in Phase 1+ agent workflows.
        """
        raise NotImplementedError("Agent process method will be implemented in subsequent phases.")
