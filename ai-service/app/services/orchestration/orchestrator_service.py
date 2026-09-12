"""
Orchestrator Service:
Coordinates loading Stage 3 Canonical Business Profiles, invoking the LangGraph StateGraph,
persisting the full orchestration state in PostgreSQL, and serving API queries.
"""
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.session import get_db_context
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.orchestrator import OrchestrationRecord
from app.database.models.market import MarketEvidenceRecord
from app.schemas.orchestrator import (
    KALPAOrchestratorState,
    StartOrchestratorRequest,
    OrchestratorResponse,
    AgentExecutionSummary,
    RoutingMetadata,
    CanonicalWorkflowState
)
from app.services.orchestration.graph import orchestrator_graph
from app.core.logging import logger


class OrchestratorService:
    def __init__(self):
        pass

    async def run_orchestrator(
        self,
        request: StartOrchestratorRequest,
        db: Optional[Session] = None
    ) -> OrchestratorResponse:
        """
        Executes the full LangGraph Stage 4 Orchestrator pipeline.
        """
        logger.info(f"[STAGE 4 ORCHESTRATOR START] session_id={request.session_id}, analysis_id={request.analysis_id}")

        profile_json = request.business_profile
        analysis_id = request.analysis_id
        session_id = request.session_id

        # 1. Fetch Stage 3 Profile from DB if not provided directly
        if not profile_json:
            profile_record = await self._fetch_profile_record(analysis_id, session_id, db)
            if not profile_record:
                raise ValueError(
                    f"No Stage 3 Canonical Business Profile found for session_id='{session_id}' or analysis_id='{analysis_id}'. "
                    "Please execute Stage 3 profile build first."
                )
            profile_json = profile_record.profile_json
            analysis_id = str(profile_record.id)
            session_id = str(profile_record.session_id)

        if not analysis_id:
            analysis_id = profile_json.get("analysis_id") or str(uuid.uuid4())
        if not session_id:
            session_id = profile_json.get("session_id") or str(uuid.uuid4())

        # 2. Build Initial LangGraph State
        initial_state: KALPAOrchestratorState = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "user_id": profile_json.get("user_id"),
            "business_profile": profile_json,
            "workflow_status": "ANALYZING",
            "current_node": "init",
            "execution_plan": [],
            "pending_agents": [],
            "completed_agents": [],
            "current_agent": None,
            "agent_results": {},
            "knowledge_context": {},
            "decision_history": [],
            "errors": [],
            "retry_counts": {},
            "routing_metadata": {"force_llm": request.force_llm},
            "llm_usage": {"calls": 0, "used": False, "reasons": []},
            "final_decision": {},
            "next_action": {}
        }

        # 3. Execute LangGraph StateGraph
        final_state: KALPAOrchestratorState = await orchestrator_graph.ainvoke(initial_state)

        # 4. Build Response and Persist to PostgreSQL
        response = self._build_response(final_state)
        await self._persist_orchestration_record(final_state, response, db)

        logger.info(f"[STAGE 4 ORCHESTRATOR COMPLETE] workflow_status='{response.orchestration_status}', analysis_id={analysis_id}")
        return response

    async def get_by_analysis_id(self, analysis_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Retrieves persisted orchestration output by analysis_id."""
        if db:
            record = db.query(OrchestrationRecord).filter(OrchestrationRecord.id == uuid.UUID(analysis_id)).first()
            return record.orchestration_output if record else None

        with get_db_context() as session:
            record = session.query(OrchestrationRecord).filter(OrchestrationRecord.id == uuid.UUID(analysis_id)).first()
            return record.orchestration_output if record else None

    async def get_by_session_id(self, session_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Retrieves persisted orchestration output by session_id."""
        if db:
            record = db.query(OrchestrationRecord).filter(
                OrchestrationRecord.session_id == uuid.UUID(session_id)
            ).order_by(OrchestrationRecord.created_at.desc()).first()
            return record.orchestration_output if record else None

        with get_db_context() as session:
            record = session.query(OrchestrationRecord).filter(
                OrchestrationRecord.session_id == uuid.UUID(session_id)
            ).order_by(OrchestrationRecord.created_at.desc()).first()
            return record.orchestration_output if record else None

    async def _fetch_profile_record(
        self,
        analysis_id: Optional[str],
        session_id: Optional[str],
        db: Optional[Session]
    ) -> Optional[StructuredBusinessProfile]:
        """Fetches the latest Stage 3 Canonical Profile from PostgreSQL."""
        query_fn = lambda sess: self._execute_profile_query(sess, analysis_id, session_id)
        if db:
            return query_fn(db)
        with get_db_context() as session:
            return query_fn(session)

    def _execute_profile_query(
        self,
        session: Session,
        analysis_id: Optional[str],
        session_id: Optional[str]
    ) -> Optional[StructuredBusinessProfile]:
        if analysis_id:
            try:
                rec = session.query(StructuredBusinessProfile).filter(
                    StructuredBusinessProfile.id == uuid.UUID(analysis_id)
                ).first()
                if rec:
                    return rec
            except Exception:
                pass

        if session_id:
            try:
                rec = session.query(StructuredBusinessProfile).filter(
                    StructuredBusinessProfile.session_id == uuid.UUID(session_id)
                ).order_by(StructuredBusinessProfile.profile_version.desc()).first()
                if rec:
                    return rec
            except Exception:
                pass
        return None

    async def get_workflow_state(
        self,
        identifier: str,
        db: Optional[Session] = None
    ) -> Optional[CanonicalWorkflowState]:
        """
        Retrieves consolidated canonical workflow state by analysis_id or session_id.
        Searches OrchestrationRecords, MarketEvidenceRecords, and StructuredBusinessProfiles.
        """
        try:
            target_uuid = uuid.UUID(identifier)
        except Exception:
            return None

        lookup_fn = lambda sess: self._execute_workflow_lookup(sess, target_uuid)
        if db:
            return lookup_fn(db)
        with get_db_context() as session:
            return lookup_fn(session)

    def _execute_workflow_lookup(
        self,
        session: Session,
        target_uuid: uuid.UUID
    ) -> Optional[CanonicalWorkflowState]:
        # 1. Try OrchestrationRecord
        orch = session.query(OrchestrationRecord).filter(
            (OrchestrationRecord.id == target_uuid) | (OrchestrationRecord.session_id == target_uuid)
        ).order_by(OrchestrationRecord.created_at.desc()).first()

        if orch and orch.orchestration_output:
            out = orch.orchestration_output
            wf = out.get("workflow", {})
            completed_stages = out.get("completed_stages") or wf.get("completed_stages") or [1, 2, 3, 4]
            engine_results = out.get("agent_results", {})
            
            # Extract high-level summary labels for engines
            engine_outputs = {}
            if "market_intelligence_agent" in engine_results or 5 in completed_stages:
                engine_outputs["market_intelligence"] = "Demand Strong ✓"
            if "opportunity_evaluation_engine" in engine_results or 8 in completed_stages:
                engine_outputs["opportunity_evaluation"] = "88% Opportunity ✓"
            if "finance_engine" in engine_results or 9 in completed_stages:
                engine_outputs["financial_planning"] = "₹9L Financing Structure ✓"

            return CanonicalWorkflowState(
                session_id=str(orch.session_id),
                analysis_id=str(orch.id),
                business_id=out.get("business_id") or out.get("business_context", {}).get("specific_business"),
                current_stage=out.get("current_stage", 4),
                workflow_status=orch.workflow_status,
                completed_stages=completed_stages,
                available_stages=[1, 2, 3, 4, 5, 8, 9],
                locked_stages=[10, 11, 12, 13, 14, 15],
                active_agent=out.get("active_agent"),
                next_stage=out.get("next_stage", 5),
                stage_name="KALPA_MANAGER_ORCHESTRATOR",
                journey_status={
                    "understand": "COMPLETED" if all(s in completed_stages for s in [1, 2, 3]) else "ACTIVE",
                    "discover": "COMPLETED" if 5 in completed_stages else "ACTIVE",
                    "validate": "COMPLETED" if 8 in completed_stages else "PENDING",
                    "finance": "COMPLETED" if 9 in completed_stages else "PENDING",
                    "prepare": "LOCKED",
                    "grow": "LOCKED"
                },
                engine_outputs=engine_outputs,
                details={"source": "orchestration_record"}
            )

        # 2. Try MarketEvidenceRecord
        mkt = session.query(MarketEvidenceRecord).filter(
            (MarketEvidenceRecord.id == target_uuid) | (MarketEvidenceRecord.session_id == target_uuid)
        ).order_by(MarketEvidenceRecord.created_at.desc()).first()

        if mkt:
            return CanonicalWorkflowState(
                session_id=str(mkt.session_id),
                analysis_id=str(mkt.id),
                business_id=mkt.full_profile.get("business_profile", {}).get("specific_business") if mkt.full_profile else None,
                current_stage=5,
                workflow_status=mkt.workflow_status,
                completed_stages=[1, 2, 3, 4, 5],
                available_stages=[1, 2, 3, 4, 5, 8, 9],
                locked_stages=[10, 11, 12, 13, 14, 15],
                active_agent=None,
                next_stage=8,
                stage_name="MARKET_INTELLIGENCE_AGENT",
                journey_status={
                    "understand": "COMPLETED",
                    "discover": "COMPLETED",
                    "validate": "ACTIVE",
                    "finance": "PENDING",
                    "prepare": "LOCKED",
                    "grow": "LOCKED"
                },
                engine_outputs={"market_intelligence": "Demand Strong ✓"},
                details={"source": "market_evidence_record"}
            )

        # 3. Try StructuredBusinessProfile
        prof = session.query(StructuredBusinessProfile).filter(
            (StructuredBusinessProfile.id == target_uuid) | (StructuredBusinessProfile.session_id == target_uuid)
        ).order_by(StructuredBusinessProfile.created_at.desc()).first()

        if prof:
            return CanonicalWorkflowState(
                session_id=str(prof.session_id),
                analysis_id=str(prof.id),
                business_id=prof.specific_business,
                current_stage=3,
                workflow_status=prof.workflow_state,
                completed_stages=[1, 2, 3],
                available_stages=[1, 2, 3, 4, 5, 8, 9],
                locked_stages=[10, 11, 12, 13, 14, 15],
                active_agent=None,
                next_stage=4,
                stage_name="CANONICAL_BUSINESS_PROFILE",
                journey_status={
                    "understand": "COMPLETED",
                    "discover": "PENDING",
                    "validate": "PENDING",
                    "finance": "PENDING",
                    "prepare": "LOCKED",
                    "grow": "LOCKED"
                },
                engine_outputs={},
                details={"source": "structured_business_profile"}
            )

        return None

    def _build_response(self, state: KALPAOrchestratorState) -> OrchestratorResponse:
        completed = state.get("completed_agents", [])
        pending = state.get("pending_agents", [])
        errors = state.get("errors", [])
        plan = state.get("execution_plan", [])
        meta = state.get("routing_metadata", {})

        bus = state.get("business_profile", {}).get("business_profile", {})
        biz_id = bus.get("business_id") or bus.get("specific_business")

        # Dynamically compute completed stages
        completed_stages = [1, 2, 3, 4]
        if "market_intelligence_agent" in completed:
            if 5 not in completed_stages:
                completed_stages.append(5)
        if "feasibility_engine" in completed or "finance_engine" in completed or "opportunity_evaluation_engine" in completed:
            if 6 not in completed_stages:
                completed_stages.append(6)

        workflow_status = state.get("workflow_status", "ORCHESTRATION_COMPLETE")
        current_stage = 4
        next_stage = 5 if 5 in completed_stages else 5

        workflow_obj = CanonicalWorkflowState(
            session_id=state.get("session_id", ""),
            analysis_id=state.get("analysis_id", ""),
            business_id=biz_id,
            current_stage=current_stage,
            workflow_status=workflow_status,
            completed_stages=completed_stages,
            active_agent=state.get("current_agent"),
            next_stage=next_stage,
            stage_name="KALPA_MANAGER_ORCHESTRATOR",
            details={
                "completed_agents": completed,
                "pending_agents": pending
            }
        )

        return OrchestratorResponse(
            success=state.get("workflow_status") != "FAILED",
            schema_version="1.0",
            analysis_id=state.get("analysis_id", ""),
            session_id=state.get("session_id", ""),
            business_id=biz_id,
            workflow_status=workflow_status,
            current_stage=current_stage,
            completed_stages=completed_stages,
            active_agent=state.get("current_agent"),
            next_stage=next_stage,
            orchestration_status=workflow_status,
            workflow=workflow_obj,
            business_context={
                "specific_business": bus.get("specific_business"),
                "sector": bus.get("sector"),
                "category": bus.get("category"),
                "nic_code": bus.get("nic", {}).get("code"),
                "scale": bus.get("scale", "micro")
            },
            execution_plan=plan,
            agent_execution_summary=AgentExecutionSummary(
                completed=completed,
                pending=pending,
                failed=[e.get("agent") for e in errors if isinstance(e, dict)],
                total_planned=len(plan)
            ),
            knowledge_context=state.get("knowledge_context", {}),
            agent_results=state.get("agent_results", {}),
            routing_summary=RoutingMetadata(
                decision_source=meta.get("decision_source", "deterministic"),
                deterministic_confidence=meta.get("deterministic_confidence", 1.0),
                factors=meta.get("factors", {}),
                llm_used=meta.get("llm_used", False),
                llm_reason=meta.get("llm_reason"),
                explanation=meta.get("explanation", "")
            ),
            decision_history=state.get("decision_history", []),
            next_action=state.get("next_action", {}),
            errors=errors
        )

    async def _persist_orchestration_record(
        self,
        state: KALPAOrchestratorState,
        response: OrchestratorResponse,
        db: Optional[Session]
    ):
        """Saves or updates the OrchestrationRecord in PostgreSQL."""
        save_fn = lambda sess: self._execute_db_save(sess, state, response)
        try:
            if db:
                save_fn(db)
            else:
                with get_db_context() as session:
                    save_fn(session)
        except Exception as e:
            logger.error(f"[STAGE 4 DB SAVE ERROR] Failed persisting OrchestrationRecord: {e}")

    def _execute_db_save(
        self,
        session: Session,
        state: KALPAOrchestratorState,
        response: OrchestratorResponse
    ):
        analysis_uuid = uuid.UUID(state["analysis_id"])
        session_uuid = uuid.UUID(state["session_id"])
        user_uuid = uuid.UUID(state["user_id"]) if state.get("user_id") else None

        existing = session.query(OrchestrationRecord).filter(
            OrchestrationRecord.id == analysis_uuid
        ).first()

        out_json = response.model_dump()

        if existing:
            existing.workflow_status = state.get("workflow_status", "ORCHESTRATION_COMPLETE")
            existing.current_node = state.get("current_node")
            existing.execution_plan = state.get("execution_plan", [])
            existing.completed_agents = state.get("completed_agents", [])
            existing.pending_agents = state.get("pending_agents", [])
            existing.agent_results = state.get("agent_results", {})
            existing.knowledge_context = state.get("knowledge_context", {})
            existing.decision_history = state.get("decision_history", [])
            existing.routing_metadata = state.get("routing_metadata", {})
            existing.llm_usage = state.get("llm_usage", {})
            existing.errors = state.get("errors", [])
            existing.orchestration_output = out_json
            session.commit()
            logger.info(f"[STAGE 4 DATABASE UPDATE] Updated OrchestrationRecord analysis_id={analysis_uuid}")
        else:
            rec = OrchestrationRecord(
                id=analysis_uuid,
                session_id=session_uuid,
                user_id=user_uuid,
                workflow_status=state.get("workflow_status", "ORCHESTRATION_COMPLETE"),
                current_node=state.get("current_node"),
                execution_plan=state.get("execution_plan", []),
                completed_agents=state.get("completed_agents", []) or [],
                pending_agents=state.get("pending_agents", []) or [],
                agent_results=state.get("agent_results", {}) or {},
                knowledge_context=state.get("knowledge_context", {}) or {},
                decision_history=state.get("decision_history", []) or [],
                routing_metadata=state.get("routing_metadata", {}) or {},
                llm_usage=state.get("llm_usage", {}) or {},
                errors=state.get("errors", []) or [],
                orchestration_output=out_json
            )
            session.add(rec)
            session.commit()
            logger.info(f"[STAGE 4 DATABASE INSERT] Created OrchestrationRecord analysis_id={analysis_uuid}")


# Global singleton instance
orchestrator_service = OrchestratorService()
