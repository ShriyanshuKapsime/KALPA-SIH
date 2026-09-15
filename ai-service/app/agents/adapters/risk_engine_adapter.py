"""
Risk Engine Adapter (Stage 11):
Connects Stage 4 Orchestrator with the Stage 11 Deterministic Risk Engine.
Synthesizes upstream structured data from Stage 6 (Market Intelligence), Stage 8 (Opportunity Evaluation),
Stage 9 (Financial Engine), Stage 10 (Entrepreneur Profile), and Curated Risk Knowledge.
"""
from typing import Dict, Any
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.risk_engine import risk_engine
from app.core.logging import logger


class RiskEngineAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="risk_engine",
            name="Deterministic Multi-Vector Risk Engine",
            description="Evaluates Market, Financial, Operational, Seasonal, Supply Chain, Competition, and Infrastructure risks with critical risk preservation.",
            capabilities=[
                "market_risk_synthesis",
                "financial_risk_dscr_evaluation",
                "operational_readiness_risk_mapping",
                "seasonal_arrival_exposure_analysis",
                "supply_chain_vulnerability_scoring",
                "competition_density_risk_calculation",
                "infrastructure_power_risk_assessment",
                "critical_risk_ceiling_enforcement"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=["entrepreneur_profile_engine"]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Executing Stage 11 Deterministic Risk Engine")

        analysis_id = state.get("analysis_id")
        session_id = state.get("session_id")
        agent_results = state.get("agent_results", {})

        # Extract upstream stage outputs from shared orchestrator state
        fin_analysis = agent_results.get("finance_engine") or state.get("financial_analysis") or {}
        opp_eval = agent_results.get("opportunity_evaluation_engine") or state.get("opportunity_evaluation") or {}
        mkt_intel = (
            agent_results.get("market_intelligence_engine") or
            agent_results.get("market_intelligence_agent") or
            state.get("market_intelligence") or
            {}
        )
        entrepreneur_readiness = agent_results.get("entrepreneur_profile_engine") or state.get("entrepreneur_readiness") or {}

        # Business and location contexts
        biz_raw = (
            business_profile.get("business_profile") or
            business_profile.get("business_context") or
            business_profile
        )
        loc_raw = (
            business_profile.get("location_profile") or
            business_profile.get("location_context") or
            state.get("location_profile") or
            {}
        )

        payload = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "business_profile": biz_raw,
            "location_profile": loc_raw,
            "financial_analysis": fin_analysis,
            "opportunity_evaluation": opp_eval,
            "market_intelligence": mkt_intel,
            "entrepreneur_readiness": entrepreneur_readiness,
            "financial_profile": state.get("financial_profile") or business_profile.get("financial_profile") or {}
        }

        # Execute Stage 11 Risk Engine
        response = risk_engine.analyze(payload)
        res_dict = response.model_dump()

        # Update orchestrator execution metadata
        res_dict["execution_metadata"] = {
            "stage": 11,
            "engine": "risk_engine",
            "status": "completed"
        }

        return res_dict
