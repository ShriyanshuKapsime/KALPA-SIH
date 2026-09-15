"""
Entrepreneur Profile Engine Adapter (Stage 10):
Connects Stage 4 Orchestrator with the Stage 10 Deterministic Entrepreneur Profile Engine.
Consumes real active analysis context (skills, experience, training, resources, operational readiness),
evaluates entrepreneur ↔ business alignment, and emits audit-grade readiness scores and support paths.
"""
from typing import Dict, Any
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.core.logging import logger


class EntrepreneurProfileAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="entrepreneur_profile_engine",
            name="Deterministic Entrepreneur Profile Engine",
            description="Evaluates entrepreneur skills, experience, training, resources, and operational readiness against benchmark requirements.",
            capabilities=[
                "skill_alignment_evaluation",
                "experience_threshold_matching",
                "training_readiness_assessment",
                "resource_availability_scoring",
                "operational_capacity_analysis",
                "targeted_clarification_generation",
                "deterministic_readiness_scoring"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=["finance_engine"]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Executing Stage 10 Deterministic Entrepreneur Profile Engine")

        analysis_id = state.get("analysis_id")
        session_id = state.get("session_id")

        # 1. Extract Entrepreneur Profile
        ep_raw = (
            state.get("entrepreneur_profile") or
            state.get("user_profile") or
            business_profile.get("entrepreneur_profile") or
            business_profile.get("user_profile") or
            business_profile.get("entrepreneur_context") or
            {}
        )

        # 2. Extract Business & Location Profile
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

        # 3. Extract Financial Context
        fin_raw = (
            state.get("financial_profile") or
            business_profile.get("financial_profile") or
            {}
        )

        payload = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "entrepreneur_profile": ep_raw,
            "business_profile": biz_raw,
            "location_profile": loc_raw,
            "financial_profile": fin_raw
        }

        # 4. Execute Entrepreneur Profile Engine
        response = entrepreneur_profile_engine.analyze(payload)
        res_dict = response.model_dump()

        # Update orchestrator execution metadata
        res_dict["execution_metadata"] = {
            "stage": 10,
            "engine": "entrepreneur_profile_engine",
            "status": "completed" if response.status == "READY" else "profile_incomplete"
        }

        return res_dict
