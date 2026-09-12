"""
Central Agent Registry for KALPA Multi-Agent System.
Provides dynamic lookup, capability inspection, dependency resolution,
and invocation routing for all registered agents.
"""
from typing import Dict, Any, List, Optional
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.agents.adapters.domain_knowledge_adapter import DomainKnowledgeAdapter
from app.agents.adapters.market_intelligence_adapter import MarketIntelligenceAdapter
from app.agents.adapters.market_intelligence_engine_adapter import MarketIntelligenceEngineAdapter
from app.agents.adapters.opportunity_evaluation_adapter import OpportunityEvaluationAdapter
from app.agents.adapters.finance_adapter import FinanceAdapter
from app.agents.adapters.feasibility_adapter import FeasibilityAdapter
from app.core.logging import logger


class AgentRegistry:
    def __init__(self):
        self._adapters: Dict[str, BaseAgentAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        self.register(DomainKnowledgeAdapter())
        self.register(MarketIntelligenceAdapter())
        self.register(MarketIntelligenceEngineAdapter())
        self.register(OpportunityEvaluationAdapter())
        self.register(FinanceAdapter())
        self.register(FeasibilityAdapter())
        logger.info(f"[AGENT REGISTRY] Registered {len(self._adapters)} agent adapters: {list(self._adapters.keys())}")

    def register(self, adapter: BaseAgentAdapter):
        self._adapters[adapter.agent_id] = adapter

    def get_agent(self, agent_id: str) -> Optional[BaseAgentAdapter]:
        return self._adapters.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "description": a.description,
                "capabilities": a.capabilities,
                "status": a.status,
                "default_priority": a.default_priority,
                "dependencies": a.dependencies
            }
            for a in self._adapters.values()
        ]

    def get_executable_agents(self, pending: List[str], completed: List[str]) -> List[str]:
        """
        Returns all pending agents whose upstream dependencies have been satisfied.
        """
        ready = []
        for agent_id in pending:
            adapter = self.get_agent(agent_id)
            if adapter and adapter.can_execute(completed):
                ready.append(agent_id)
        return ready

    async def execute_agent(
        self,
        agent_id: str,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        adapter = self.get_agent(agent_id)
        if not adapter:
            raise ValueError(f"Agent '{agent_id}' is not registered in the KALPA Agent Registry.")
        return await adapter.execute(business_profile, knowledge_context, state)


# Global singleton instance
agent_registry = AgentRegistry()
