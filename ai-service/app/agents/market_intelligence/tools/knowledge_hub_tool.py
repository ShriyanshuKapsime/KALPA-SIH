"""
Knowledge Hub Tool (Tool 9).
Queries Stage 4.5 Knowledge Hub to retrieve verified static benchmarks (catchment radii,
seasonality multipliers, demand drivers, and dynamic dataset dependencies).
"""
import time
from typing import Dict, Any, Union
from app.agents.market_intelligence.tools.base_tool import BaseMarketTool, ToolExecutionContext, ToolResult
from app.knowledge.services.knowledge_service import KnowledgeService
from app.schemas.market import SeasonalityEvidenceItem, MarketExecutionContext


class KnowledgeHubTool(BaseMarketTool):
    def __init__(self, knowledge_service: KnowledgeService = None):
        super().__init__(
            name="knowledge_hub_tool",
            description="Fetches static domain benchmarks, catchment rules, seasonality factors, and dynamic data specs from Stage 4.5.",
            supported_requirements=[
                "market_knowledge_pack",
                "catchment_benchmarks",
                "seasonality_factors",
                "saturation_benchmarks",
                "static_knowledge_context"
            ]
        )
        self.knowledge_service = knowledge_service or KnowledgeService()

    async def execute(self, context: Union[ToolExecutionContext, MarketExecutionContext]) -> ToolResult:
        start_t = time.perf_counter()

        if isinstance(context, MarketExecutionContext):
            business_id = context.business.business_id.lower().strip()
        else:
            bus_profile = context.business_profile or {}
            bus_sec = bus_profile.get("business_profile") or {}
            business_id = (
                context.canonical_business.business_id if context.canonical_business else
                bus_profile.get("business_id") or bus_sec.get("business_id") or "general"
            ).lower().strip()

        # Fetch MarketKnowledgePack from Stage 4.5
        market_pack = self.knowledge_service.get_market_context(business_id)

        seasonality_items = []
        if market_pack.seasonality_factors:
            factors = market_pack.seasonality_factors
            peak_months = [m.upper() for m, v in factors.items() if v >= 1.15]
            lean_months = [m.upper() for m, v in factors.items() if v <= 0.90]

            seasonality_items.append(
                SeasonalityEvidenceItem(
                    factor_name=f"{market_pack.business_title} Annual Cyclicality",
                    peak_months=peak_months,
                    lean_months=lean_months,
                    seasonal_notes=market_pack.seasonality_notes or "Demand fluctuations governed by agricultural cycles and festivals.",
                    monthly_multipliers=factors,
                    data_status="OFFICIAL_STATIC_DATA",
                    source={
                        "source_id": (market_pack.provenance.source_id if market_pack.provenance else "NABARD_BENCHMARK_2024"),
                        "organization": (market_pack.provenance.organization if market_pack.provenance else "NABARD / MSME Ministry"),
                        "source_type": "OFFICIAL_BENCHMARK",
                        "retrieval_method": "STATIC_KNOWLEDGE"
                    }
                )
            )

        elapsed = (time.perf_counter() - start_t) * 1000.0

        return ToolResult(
            tool_name=self.name,
            status="success" if market_pack.available else "partial",
            data_status="OFFICIAL_STATIC_DATA",
            geographic_precision="national",
            target_geographic_precision="village",
            data_geographic_precision="national",
            confidence=0.94 if market_pack.available else 0.70,
            source={
                "source_id": "STAGE-4.5-KNOWLEDGE-HUB",
                "organization": "KALPA Domain Knowledge & Benchmark Hub",
                "source_type": "CURATED_KNOWLEDGE_PACK",
                "retrieval_method": "STATIC_KNOWLEDGE"
            },
            data={
                "market_knowledge_pack": market_pack.model_dump(),
                "seasonality_evidence": [s.model_dump() for s in seasonality_items]
            },
            execution_time_ms=round(elapsed, 2)
        )
