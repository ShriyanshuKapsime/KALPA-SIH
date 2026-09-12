"""
Base Agent Adapter Interface.
Provides the abstraction contract for both production adapters (e.g. Domain Knowledge)
and prototype adapters (e.g. Market Intelligence, Finance, Feasibility) in Stage 4.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseAgentAdapter(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: List[str],
        status: str = "available",  # available | prototype | future
        default_priority: str = "HIGH",  # HIGH | MEDIUM | LOW
        dependencies: Optional[List[str]] = None,
        max_retries: int = 2
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.status = status
        self.default_priority = default_priority
        self.dependencies = dependencies or []
        self.max_retries = max_retries

    def can_execute(self, completed_agents: List[str]) -> bool:
        """Returns True if all required upstream dependencies have completed."""
        return all(dep in completed_agents for dep in self.dependencies)

    @abstractmethod
    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes the agent adapter logic and returns a structured output payload.
        """
        pass
