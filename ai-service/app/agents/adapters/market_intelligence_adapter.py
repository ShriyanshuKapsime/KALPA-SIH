"""
Market Intelligence Agent Adapter:
Connects Stage 4 Orchestrator with the Stage 5 Market Intelligence LangGraph workflow.
Performs autonomous market evidence collection, location resolution, and structured profile generation.
"""
from typing import Dict, Any
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.agents.market_intelligence.market_agent import market_intelligence_agent
from app.core.logging import logger


class MarketIntelligenceAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="market_intelligence_agent",
            name="Market Intelligence Agent",
            description="Performs autonomous market data collection, GPS/text location resolution, demographic profiling, competitor discovery, and supply access evidence retrieval.",
            capabilities=[
                "reverse_geocoding",
                "location_conflict_detection",
                "demographic_evidence_retrieval",
                "competitor_discovery",
                "demand_indicator_synthesis",
                "supply_access_mapping",
                "infrastructure_validation",
                "economic_purchasing_power_proxies",
                "explainable_quality_scoring"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=["domain_knowledge_agent"]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Invoking Stage 5 Market Intelligence Agent")

        analysis_id = state.get("analysis_id")
        session_id = state.get("session_id")
        user_id = state.get("user_id")
        force_llm = state.get("routing_metadata", {}).get("force_llm", False)

        evidence_profile = await market_intelligence_agent.collect_evidence(
            business_profile=business_profile,
            analysis_id=analysis_id,
            session_id=session_id,
            user_id=user_id,
            force_llm=force_llm
        )

        return evidence_profile.model_dump()
