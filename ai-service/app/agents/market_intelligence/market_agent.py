"""
Market Intelligence Agent Interface (Stage 5).
Responsible for:
- Autonomous market data collection and evidence retrieval
- Context normalization and semantic isolation
- Location hierarchy resolution and conflict detection
- Tool execution, cache isolation, and retry orchestration
- Structured raw market evidence assembly (MarketEvidenceProfile)
"""
import uuid
from typing import Dict, Any, Optional
from app.agents.base import BaseKalpaAgent, AgentState
from app.agents.market_intelligence.graph import market_intelligence_graph
from app.schemas.market import MarketEvidenceProfile
from app.database.session import get_db_context
from app.database.models.market import MarketEvidenceRecord
from app.core.logging import logger


class MarketIntelligenceAgent(BaseKalpaAgent):
    def __init__(self):
        super().__init__(
            agent_name="market_intelligence_agent",
            description="Coordinates spatial location resolution, demographic profiling, competitor discovery, and evidence collection."
        )

    async def process(self, state: AgentState) -> AgentState:
        """
        Processes an AgentState using the LangGraph Market Intelligence workflow.
        """
        profile = state.extracted_data.get("business_profile") or state.extracted_data
        result_profile = await self.collect_evidence(
            business_profile=profile,
            analysis_id=state.business_id or str(uuid.uuid4()),
            session_id=state.session_id or str(uuid.uuid4()),
            user_id=state.user_id
        )
        state.extracted_data["market_evidence_profile"] = result_profile.model_dump()
        state.current_node = "market_evidence_ready"
        return state

    async def collect_evidence(
        self,
        business_profile: Dict[str, Any],
        analysis_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        force_llm: bool = False,
        force_refresh: bool = False
    ) -> MarketEvidenceProfile:
        """
        Primary execution entry point for Stage 5 Market Intelligence Agent.
        Enforces idempotency: Returns existing completed record without invoking Sarvam LLM
        or running tools unless force_refresh is True.
        """
        if not force_refresh and analysis_id:
            try:
                target_uuid = uuid.UUID(str(analysis_id))
                with get_db_context() as db:
                    if db:
                        rec = db.query(MarketEvidenceRecord).filter(MarketEvidenceRecord.id == target_uuid).first()
                        if rec and rec.full_profile and rec.workflow_status in ("MARKET_EVIDENCE_COLLECTED", "MARKET_EVIDENCE_READY", "COMPLETE"):
                            logger.info(
                                f"[STAGE 5 IDEMPOTENCY HIT] Returning existing MarketEvidenceRecord for analysis_id='{analysis_id}'. "
                                "Zero Sarvam LLM calls and zero tool executions consumed."
                            )
                            return MarketEvidenceProfile(**rec.full_profile)
            except Exception as e:
                logger.debug(f"[STAGE 5 IDEMPOTENCY CHECK] DB lookup note: {e}")

        initial_state = {
            "analysis_id": analysis_id or str(uuid.uuid4()),
            "session_id": session_id or str(uuid.uuid4()),
            "user_id": user_id,
            "business_profile": business_profile,
            "force_llm": force_llm,
            "force_refresh": force_refresh,
            "workflow_status": "MARKET_EVIDENCE_PENDING",
            "current_node": "init",
            "errors": []
        }

        final_state = await market_intelligence_graph.ainvoke(initial_state)
        final_doc = final_state.get("final_evidence_profile", {})
        return MarketEvidenceProfile(**final_doc)

    async def run(
        self,
        request_or_profile: Any,
        analysis_id: Optional[str] = None,
        session_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> MarketEvidenceProfile:
        """
        Convenience execution helper supporting dict payloads or request objects.
        """
        if isinstance(request_or_profile, dict):
            bp = request_or_profile.get("business_profile") or request_or_profile
            f_refresh = request_or_profile.get("force_refresh", force_refresh)
            f_llm = request_or_profile.get("force_llm", False)
            a_id = request_or_profile.get("analysis_id", analysis_id)
            s_id = request_or_profile.get("session_id", session_id)
            u_id = request_or_profile.get("user_id", None)
        else:
            bp = getattr(request_or_profile, "business_profile", request_or_profile)
            f_refresh = getattr(request_or_profile, "force_refresh", force_refresh)
            f_llm = getattr(request_or_profile, "force_llm", False)
            a_id = getattr(request_or_profile, "analysis_id", analysis_id)
            s_id = getattr(request_or_profile, "session_id", session_id)
            u_id = getattr(request_or_profile, "user_id", None)

        return await self.collect_evidence(
            business_profile=bp,
            analysis_id=a_id,
            session_id=s_id,
            user_id=u_id,
            force_llm=f_llm,
            force_refresh=f_refresh
        )


market_intelligence_agent = MarketIntelligenceAgent()
