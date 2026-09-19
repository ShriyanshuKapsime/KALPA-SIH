"""
Market Intelligence API Router (Stage 5).
Exposes REST endpoints for autonomous market evidence collection, retrieval,
execution inspection, retry, and tool health monitoring with strict business context integrity.
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.market import (
    CollectMarketEvidenceRequest,
    CollectMarketEvidenceResponse,
    MarketEvidenceProfile,
    ToolHealthReport,
    ToolHealthItem,
    RetryExecutionRequest,
)
from app.services.market_intelligence_engine import Stage6Output, market_intelligence_engine
from app.agents.market_intelligence.market_agent import market_intelligence_agent
from app.agents.market_intelligence.tools.tool_registry import market_tool_registry
from app.database.session import get_db
from app.database.models.market import MarketEvidenceRecord
from app.database.models.profile import StructuredBusinessProfile
from app.core.logging import logger

router = APIRouter(prefix="/market-intelligence", tags=["Stage 5 — Market Intelligence Agent"])


@router.post(
    "/collect",
    response_model=CollectMarketEvidenceResponse,
    summary="Trigger Autonomous Market Evidence Collection",
    description="Invokes Stage 5 LangGraph agent to resolve location, plan requirements, execute tools, and compile raw market evidence."
)
async def collect_market_evidence(
    req: CollectMarketEvidenceRequest,
    db: Session = Depends(get_db)
):
    analysis_id = req.analysis_id or str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())
    logger.info(f"[API COLLECT] Request received: analysis_id={analysis_id}, session_id={session_id}, force_refresh={req.force_refresh}, force_llm={req.force_llm}")

    profile_data = req.business_profile
    if not profile_data and req.analysis_id:
        try:
            # Try to load existing canonical profile from DB
            analysis_uuid = uuid.UUID(req.analysis_id)
            stmt = select(StructuredBusinessProfile).where(StructuredBusinessProfile.id == analysis_uuid)
            res = db.execute(stmt).scalar_one_or_none()
            if res:
                profile_data = res.profile_json if hasattr(res, 'profile_json') and res.profile_json else getattr(res, 'full_profile', None)
        except Exception as e:
            logger.warning(f"[API COLLECT] Could not load profile from DB: {e}")

    if not profile_data:
        if not req.business_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="BUSINESS_CLASSIFICATION_FAILED: No business_profile or business_id provided. "
                       "Cannot default to any business. Please provide explicit business context."
            )
        req_biz = req.business_id
        profile_data = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "business_id": req_biz,
            "business_profile": {
                "business_id": req_biz,
                "specific_business": req_biz.replace("_", " ").title(),
                "normalized_concept": req_biz.replace("_", " ")
            }
        }

    try:
        evidence_profile = await market_intelligence_agent.collect_evidence(
            business_profile=profile_data,
            analysis_id=analysis_id,
            session_id=session_id,
            force_llm=req.force_llm,
            force_refresh=req.force_refresh
        )

        return CollectMarketEvidenceResponse(
            success=True,
            analysis_id=analysis_id,
            session_id=session_id,
            status=evidence_profile.workflow.status,
            evidence_profile=evidence_profile
        )
    except Exception as e:
        logger.error(f"[API COLLECT ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing Market Intelligence Agent: {str(e)}"
        )


@router.get(
    "/tools/health",
    response_model=ToolHealthReport,
    summary="Stage 5 Tool Ecosystem Health Check",
    description="Returns live operational health and metadata for all 10 registered market tools."
)
async def get_tool_health():
    report_dict = await market_tool_registry.get_health_report()
    tool_items = [
        ToolHealthItem(
            tool=t.get("tool") or t["name"],
            tool_name=t["name"],
            status=t.get("status", "available"),
            latency_ms=t.get("latency_ms", 1.5),
            details=t
        )
        for t in report_dict["tools"]
    ]
    return ToolHealthReport(
        status="success",
        total_tools=report_dict["total_tools"],
        healthy_tools=report_dict["healthy_tools"],
        tools=tool_items
    )


@router.get(
    "/{analysis_id}",
    response_model=MarketEvidenceProfile,
    summary="Get Market Evidence Profile by Analysis ID"
)
async def get_market_evidence_profile(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        stmt = select(MarketEvidenceRecord).where(MarketEvidenceRecord.id == analysis_uuid)
        res = db.execute(stmt).scalar_one_or_none()
        if res and res.full_profile:
            return MarketEvidenceProfile(**res.full_profile)
    except Exception as e:
        logger.warning(f"[API GET] DB lookup failed: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No market evidence profile found for analysis_id='{analysis_id}'. Use POST /market-intelligence/collect to generate evidence."
    )


@router.get(
    "/{analysis_id}/evidence",
    summary="Get Raw Market Evidence Categories"
)
async def get_market_evidence_data(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    profile = await get_market_evidence_profile(analysis_id, db)
    return profile.market_evidence


@router.get(
    "/{analysis_id}/execution",
    summary="Get Execution Metadata & Collection Plan Trace"
)
async def get_market_execution_trace(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    profile = await get_market_evidence_profile(analysis_id, db)
    return {
        "analysis_id": profile.analysis_id,
        "workflow": profile.workflow,
        "business_context": profile.business_context,
        "collection_plan": profile.collection_plan,
        "execution_metadata": profile.execution_metadata,
        "location_context": profile.location_context,
        "evidence_quality": profile.evidence_quality,
        "evidence_gaps": profile.evidence_gaps
    }


@router.post(
    "/analyze",
    response_model=Stage6Output,
    summary="Stage 6 Deterministic Market Intelligence Engine",
    description="Transforms raw Stage 5 market evidence into structured indicators, benchmark comparisons, explainable provenance, and Stage 7 ML market features."
)
async def analyze_market_intelligence(
    stage5_payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    logger.info("[API STAGE 6] Received market intelligence analysis request")
    try:
        # If payload only has analysis_id and no market_evidence, attempt to load from DB
        analysis_id = stage5_payload.get("analysis_id")
        if analysis_id and not stage5_payload.get("market_evidence") and not stage5_payload.get("evidence_profile"):
            try:
                target_uuid = uuid.UUID(analysis_id)
                rec = db.query(MarketEvidenceRecord).filter(
                    (MarketEvidenceRecord.id == target_uuid) | (MarketEvidenceRecord.session_id == target_uuid)
                ).first()
                if rec and rec.full_profile:
                    stage5_payload = rec.full_profile
            except Exception as e:
                logger.warning(f"[API STAGE 6] DB lookup note: {e}")

        result = market_intelligence_engine.analyze(stage5_payload)
        return result
    except Exception as e:
        logger.error(f"[API STAGE 6 ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 6 Market Intelligence Engine error: {str(e)}"
        )


@router.post(
    "/{analysis_id}/retry",
    response_model=CollectMarketEvidenceResponse,
    summary="Retry Market Evidence Collection for Failed Tools"
)
async def retry_market_evidence_collection(
    analysis_id: str,
    req: RetryExecutionRequest,
    db: Session = Depends(get_db)
):
    # Re-trigger data collection with force_refresh
    evidence_profile = await market_intelligence_agent.collect_evidence(
        business_profile={"business_id": analysis_id, "business_profile": {"business_id": analysis_id}},
        analysis_id=analysis_id,
        session_id=str(uuid.uuid4()),
        force_refresh=req.force_refresh
    )
    return CollectMarketEvidenceResponse(
        success=True,
        analysis_id=analysis_id,
        session_id=evidence_profile.session_id,
        status=evidence_profile.workflow.status,
        evidence_profile=evidence_profile
    )

