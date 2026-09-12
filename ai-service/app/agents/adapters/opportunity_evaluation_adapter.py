"""
Opportunity Evaluation Engine Adapter:
Connects Stage 4 Orchestrator with the Stage 8 Deterministic Opportunity Evaluation Engine.
Consumes structured Stage 6 Market Intelligence indicators, checks for Stage 7 ML Demand Prediction
(gracefully skipping Stage 7 if deferred for MVP), and executes deterministic market opportunity synthesis.
"""
from typing import Dict, Any
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.opportunity_evaluation_engine import opportunity_evaluation_engine
from app.core.logging import logger


class OpportunityEvaluationAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="opportunity_evaluation_engine",
            name="Opportunity Evaluation Engine",
            description="Evaluates whether the proposed MSME business has a viable market opportunity at the target location.",
            capabilities=[
                "deterministic_opportunity_scoring",
                "demand_source_abstraction",
                "critical_market_constraint_evaluation",
                "component_opportunity_synthesis",
                "factor_explanation_generation",
                "audit_grade_calculation_provenance"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=["market_intelligence_engine"]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Executing Stage 8 Opportunity Evaluation Engine")

        # 1. Retrieve Stage 6 output from Orchestrator Shared State
        agent_results = state.get("agent_results", {})
        stage6_result = agent_results.get("market_intelligence_engine") or {}

        # Fallback if stage6_result was not produced: check stage 5 or envelope
        if not stage6_result.get("market_indicators"):
            stage5_res = agent_results.get("market_intelligence_agent") or {}
            analysis_id = state.get("analysis_id")
            session_id = state.get("session_id")
            stage6_result = {
                "analysis_id": analysis_id,
                "session_id": session_id,
                "business_context": business_profile.get("business_profile") or business_profile,
                "location_context": business_profile.get("location_profile") or {},
                "market_indicators": stage5_res.get("market_indicators") or {}
            }

        # 2. Check for optional Stage 7 ML Demand Prediction
        demand_prediction = (
            state.get("demand_prediction") or
            agent_results.get("demand_prediction_ml") or
            agent_results.get("demand_prediction")
        )

        # Explicitly record Stage 7 workflow status if deferred for MVP
        if not demand_prediction:
            logger.info(
                f"[{self.agent_id.upper()}] Stage 7 ML model deferred/unavailable. "
                "Operating in MVP Mode using Stage 6 Deterministic Demand Evidence."
            )
            stage_7_status = {
                "status": "SKIPPED",
                "reason": "ML model integration deferred for MVP",
                "fallback": "STAGE_6_DETERMINISTIC_DEMAND_EVIDENCE"
            }
        else:
            stage_7_status = {
                "status": "COMPLETED",
                "source": "STAGE_7_ML",
                "details": demand_prediction
            }

        # Update orchestrator state workflow metadata for Stage 7
        workflow_stages = state.setdefault("workflow_stages", {})
        workflow_stages["stage_7"] = stage_7_status

        # 3. Assemble Stage 8 Engine Request
        payload = {
            "analysis_id": state.get("analysis_id") or stage6_result.get("analysis_id"),
            "session_id": state.get("session_id") or stage6_result.get("session_id"),
            "business_context": business_profile.get("business_profile") or stage6_result.get("business_context", {}),
            "location_context": business_profile.get("location_profile") or stage6_result.get("location_context", {}),
            "market_intelligence": stage6_result,
            "demand_prediction": demand_prediction
        }

        # 4. Execute Stage 8 Deterministic Engine
        response = opportunity_evaluation_engine.evaluate(payload)
        return response.model_dump()
