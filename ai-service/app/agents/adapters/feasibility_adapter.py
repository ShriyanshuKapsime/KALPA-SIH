"""
Feasibility Engine Adapter (Stage 12):
Connects Stage 4 Orchestrator with the Stage 12 Deterministic Feasibility Synthesis Engine.
Consumes real structured outputs from:
- Stage 8: Opportunity Evaluation Engine
- Stage 9: Deterministic Financial Engine
- Stage 10: Entrepreneur Profile Engine
- Stage 11: Enterprise Risk Engine
- Stage 6 / 5: Market Intelligence Evidence
"""
import uuid
from typing import Dict, Any, Optional
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.feasibility_engine import feasibility_engine
from app.schemas.feasibility import FeasibilityEvaluationRequest
from app.database.session import get_db_context
from app.database.models.feasibility import FeasibilityResult
from app.core.logging import logger


class FeasibilityAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="feasibility_engine",
            name="Stage 12 Feasibility Synthesis Engine",
            description="Evaluates composite business viability, 4-pillar multivariate synthesis, critical constraints, ML model prediction, dynamic SWOT, and pivot advisory.",
            capabilities=[
                "composite_viability_scoring",
                "four_pillar_synthesis",
                "critical_gates_evaluation",
                "dynamic_swot_generation",
                "strategic_pivot_advisory",
                "calculation_provenance_audit"
            ],
            status="production_ready",
            default_priority="HIGH",
            dependencies=[
                "opportunity_evaluation_engine",
                "finance_engine",
                "entrepreneur_profile_engine",
                "risk_engine"
            ]
        )

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Executing Stage 12 Feasibility Synthesis Engine")

        analysis_id = state.get("analysis_id") or business_profile.get("analysis_id") or str(uuid.uuid4())
        session_id = state.get("session_id") or business_profile.get("session_id") or str(uuid.uuid4())
        agent_results = state.get("agent_results", {})

        # 1. Extract upstream structured data
        opp_data = (
            agent_results.get("opportunity_evaluation_engine") or
            state.get("opportunity_evaluation") or
            state.get("opportunity_result") or
            {}
        )
        fin_data = (
            agent_results.get("finance_engine") or
            state.get("financial_analysis") or
            state.get("financial_profile") or
            {}
        )
        ep_data = (
            agent_results.get("entrepreneur_profile_engine") or
            state.get("entrepreneur_readiness") or
            state.get("entrepreneur_profile") or
            {}
        )
        risk_data = (
            agent_results.get("risk_engine") or
            state.get("risk_analysis") or
            {}
        )
        raw_market = (
            agent_results.get("market_intelligence_engine") or
            agent_results.get("market_intelligence_agent") or
            state.get("market_intelligence") or
            knowledge_context
        )

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

        bus_name = (
            biz_raw.get("specific_business") or
            biz_raw.get("business_name") or
            "Target Micro-Enterprise"
        )

        # Log required execution marker
        logger.info(
            f"[FEASIBILITY INPUT] analysis_id={analysis_id}, bus_name='{bus_name}', "
            f"opportunity={bool(opp_data)}, finance={bool(fin_data)}, "
            f"entrepreneur={bool(ep_data)}, risk={bool(risk_data)}"
        )

        req = FeasibilityEvaluationRequest(
            analysis_id=analysis_id,
            session_id=session_id,
            business_profile=biz_raw,
            location_profile=loc_raw,
            opportunity_result=opp_data,
            financial_analysis=fin_data,
            entrepreneur_readiness=ep_data,
            risk_analysis=risk_data
        )

        # 2. Execute Stage 12 Feasibility Engine
        response = feasibility_engine.evaluate_feasibility(
            request=req,
            raw_market_evidence=raw_market
        )

        # Log required result marker
        logger.info(
            f"[FEASIBILITY RESULT] score={response.overall_feasibility_score:.1f}, "
            f"decision='{response.decision}', recommendation='{response.recommendation}'"
        )

        res_dict = response.model_dump()
        res_dict["status"] = "production_complete"
        res_dict["execution_metadata"] = {
            "stage": 12,
            "engine": "feasibility_engine",
            "status": "completed"
        }

        # 3. Persist Feasibility Result in PostgreSQL
        try:
            target_uuid = uuid.UUID(analysis_id)
            with get_db_context() as db_session:
                if db_session:
                    existing = db_session.query(FeasibilityResult).filter(
                        (FeasibilityResult.id == target_uuid) | (FeasibilityResult.session_id == target_uuid)
                    ).first()

                    if existing:
                        existing.overall_feasibility_score = response.overall_feasibility_score
                        existing.viability_status = response.decision
                        existing.recommendation = response.recommendation
                        existing.confidence_score = response.confidence_score
                        existing.market_score = response.pillar_scores.get("market_opportunity", {}).score if hasattr(response.pillar_scores.get("market_opportunity"), "score") else 0.0
                        existing.financial_score = response.pillar_scores.get("financial_viability", {}).score if hasattr(response.pillar_scores.get("financial_viability"), "score") else 0.0
                        existing.entrepreneur_fit_score = response.pillar_scores.get("entrepreneur_readiness", {}).score if hasattr(response.pillar_scores.get("entrepreneur_readiness"), "score") else 0.0
                        existing.risk_resilience_score = response.pillar_scores.get("risk_resilience", {}).score if hasattr(response.pillar_scores.get("risk_resilience"), "score") else 0.0
                        existing.pillar_scores = res_dict.get("pillar_scores", {})
                        existing.critical_gates = res_dict.get("critical_gates", [])
                        existing.positive_drivers = res_dict.get("positive_drivers", [])
                        existing.key_constraints = res_dict.get("key_constraints", [])
                        existing.conditions = res_dict.get("conditions", [])
                        existing.strengths = res_dict.get("dynamic_swot", {}).get("strengths", [])
                        existing.weaknesses = res_dict.get("dynamic_swot", {}).get("weaknesses", [])
                        existing.opportunities = res_dict.get("dynamic_swot", {}).get("opportunities", [])
                        existing.threats = res_dict.get("dynamic_swot", {}).get("threats", [])
                        existing.pivot_recommendations = res_dict.get("pivot_recommendations", [])
                        existing.calculation_provenance = res_dict.get("calculation_provenance", [])
                        existing.ml_prediction = res_dict.get("ml_prediction", {})
                        db_session.commit()
                        logger.info(f"[STAGE 12 DB] Updated FeasibilityResult for analysis_id={target_uuid}")
                    else:
                        rec = FeasibilityResult(
                            id=target_uuid,
                            session_id=uuid.UUID(session_id) if session_id else target_uuid,
                            overall_feasibility_score=response.overall_feasibility_score,
                            viability_status=response.decision,
                            recommendation=response.recommendation,
                            confidence_score=response.confidence_score,
                            market_score=response.pillar_scores.get("market_opportunity", {}).score if hasattr(response.pillar_scores.get("market_opportunity"), "score") else 0.0,
                            financial_score=response.pillar_scores.get("financial_viability", {}).score if hasattr(response.pillar_scores.get("financial_viability"), "score") else 0.0,
                            entrepreneur_fit_score=response.pillar_scores.get("entrepreneur_readiness", {}).score if hasattr(response.pillar_scores.get("entrepreneur_readiness"), "score") else 0.0,
                            risk_resilience_score=response.pillar_scores.get("risk_resilience", {}).score if hasattr(response.pillar_scores.get("risk_resilience"), "score") else 0.0,
                            pillar_scores=res_dict.get("pillar_scores", {}),
                            critical_gates=res_dict.get("critical_gates", []),
                            positive_drivers=res_dict.get("positive_drivers", []),
                            key_constraints=res_dict.get("key_constraints", []),
                            conditions=res_dict.get("conditions", []),
                            strengths=res_dict.get("dynamic_swot", {}).get("strengths", []),
                            weaknesses=res_dict.get("dynamic_swot", {}).get("weaknesses", []),
                            opportunities=res_dict.get("dynamic_swot", {}).get("opportunities", []),
                            threats=res_dict.get("dynamic_swot", {}).get("threats", []),
                            pivot_recommendations=res_dict.get("pivot_recommendations", []),
                            calculation_provenance=res_dict.get("calculation_provenance", []),
                            ml_prediction=res_dict.get("ml_prediction", {})
                        )
                        db_session.add(rec)
                        db_session.commit()
                        logger.info(f"[STAGE 12 DB] Created FeasibilityResult for analysis_id={target_uuid}")
        except Exception as db_err:
            logger.warning(f"[FEASIBILITY ADAPTER DB NOTE] {db_err}")

        return res_dict
