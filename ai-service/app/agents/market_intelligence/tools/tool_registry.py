"""
Central Tool Registry for Stage 5 Market Intelligence Tools.
Manages discovery, registration, input validation, and health checks across the 10 tools.
"""
from typing import Dict, Any, List, Optional
from app.agents.market_intelligence.tools.base_tool import BaseMarketTool
from app.agents.market_intelligence.tools.location_tool import LocationIntelligenceTool
from app.agents.market_intelligence.tools.demographics_tool import DemographicsTool
from app.agents.market_intelligence.tools.competitor_tool import CompetitorDiscoveryTool
from app.agents.market_intelligence.tools.demand_evidence_tool import DemandEvidenceTool
from app.agents.market_intelligence.tools.supply_access_tool import SupplyAccessTool
from app.agents.market_intelligence.tools.infrastructure_tool import InfrastructureAccessTool
from app.agents.market_intelligence.tools.economic_tool import EconomicPurchasingPowerTool
from app.agents.market_intelligence.tools.dataset_retrieval_tool import DatasetRetrievalTool
from app.agents.market_intelligence.tools.knowledge_hub_tool import KnowledgeHubTool
from app.agents.market_intelligence.tools.demand_prediction_adapter import DemandPredictionAdapter
from app.core.logging import logger


class MarketToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseMarketTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        tools_list = [
            LocationIntelligenceTool(),
            DemographicsTool(),
            CompetitorDiscoveryTool(),
            DemandEvidenceTool(),
            SupplyAccessTool(),
            InfrastructureAccessTool(),
            EconomicPurchasingPowerTool(),
            DatasetRetrievalTool(),
            KnowledgeHubTool(),
            DemandPredictionAdapter(),
        ]
        for t in tools_list:
            self.register(t)
        logger.info(f"[STAGE 5 TOOL REGISTRY] Registered {len(self._tools)} market tools: {list(self._tools.keys())}")

    def register(self, tool: BaseMarketTool):
        self._tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[BaseMarketTool]:
        return self._tools.get(tool_name)

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "supported_requirements": t.supported_requirements
            }
            for t in self._tools.values()
        ]

    async def get_health_report(self) -> Dict[str, Any]:
        """Runs health checks on all registered tools."""
        reports = []
        for name, tool in self._tools.items():
            h = await tool.health_check()
            reports.append(h)
        return {
            "status": "success",
            "total_tools": len(self._tools),
            "healthy_tools": sum(1 for r in reports if r.get("status") in ["available", "healthy"]),
            "tools": reports
        }


# Global singleton instance
market_tool_registry = MarketToolRegistry()
