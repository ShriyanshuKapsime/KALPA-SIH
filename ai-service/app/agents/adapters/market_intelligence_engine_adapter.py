"""
Market Intelligence Engine Adapter:
Connects Stage 4 Orchestrator with the Stage 6 Deterministic Market Intelligence Engine.
Consumes raw verified Stage 5 market evidence, executes deterministic indicator synthesis,
and generates structured market features for Stage 7 ML Demand Prediction.
"""
from typing import Dict, Any
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.market_intelligence_engine import market_intelligence_engine
from app.core.logging import logger


class MarketIntelligenceEngineAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="market_intelligence_engine",
            name="Market Intelligence Engine",
            description="Transforms raw Stage 5 market evidence into structured indicators, benchmark comparisons, explainable provenance, and ML market features.",
            capabilities=[
                "deterministic_data_cleaning",
                "haversine_catchment_analysis",
                "three_tier_competition_pressure",
                "demand_evidence_synthesis",
                "infrastructure_gap_validation",
                "supply_ecosystem_mapping",
                "annual_seasonality_volatility",
                "net_market_capacity_estimation",
                "stage7_feature_contract_generation"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=["market_intelligence_agent"]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Invoking Stage 6 Market Intelligence Engine")

        # 1. Retrieve Stage 5 Raw Evidence from Orchestrator Shared State
        stage5_result = state.get("agent_results", {}).get("market_intelligence_agent") or {}

        # Fallback if stage5_result is minimal: construct envelope using state metadata and business_profile
        if not stage5_result.get("market_evidence"):
            analysis_id = state.get("analysis_id")
            session_id = state.get("session_id")
            stage5_result = {
                "analysis_id": analysis_id,
                "session_id": session_id,
                "business_context": business_profile.get("business_profile") or business_profile,
                "location_context": business_profile.get("location_profile") or {},
                "market_evidence": stage5_result.get("market_evidence") or {}
            }

        # 2. Execute Stage 6 Deterministic Engine
        stage6_output = market_intelligence_engine.analyze(stage5_result)

        return stage6_output.model_dump()
