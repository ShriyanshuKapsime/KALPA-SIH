"""
Opportunity Evaluation API Router (Stage 8).
Exposes REST endpoints for deterministic market opportunity evaluation,
explainable calculation inspection, and health status.
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.opportunity_evaluation import (
    OpportunityEvaluationRequest,
    OpportunityEvaluationResponse
)
from app.services.opportunity_evaluation_engine import (
    opportunity_evaluation_engine,
    OPPORTUNITY_WEIGHTS
)
from app.database.session import get_db
from app.database.models.market import MarketEvidenceRecord
from app.core.logging import logger

router = APIRouter(prefix="/opportunity-evaluation", tags=["Stage 8 — Opportunity Evaluation Engine"])


@router.post(
    "/analyze",
    response_model=OpportunityEvaluationResponse,
    summary="Stage 8 Deterministic Opportunity Evaluation Engine",
    description="Evaluates if the business has a viable market opportunity at the target location by synthesizing Demand, Competition, Infrastructure, Supply, Market Access, and Market Capacity."
)
async def analyze_opportunity(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    logger.info("[API STAGE 8] Received opportunity evaluation analysis request")
    try:
        analysis_id = payload.get("analysis_id")

        # If payload only contains analysis_id and no market indicators, attempt lookup from DB
        if analysis_id and not payload.get("market_indicators") and not payload.get("market_intelligence"):
            try:
                rec = db.query(MarketEvidenceRecord).filter(MarketEvidenceRecord.analysis_id == analysis_id).first()
                if rec and rec.full_profile:
                    # Enrich payload with Stage 5 / Stage 6 evidence from DB
                    payload["market_intelligence"] = rec.full_profile
            except Exception as e:
                logger.warning(f"[API STAGE 8] DB lookup note: {e}")

        result = opportunity_evaluation_engine.evaluate(payload)
        return result
    except Exception as e:
        logger.error(f"[API STAGE 8 ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 8 Opportunity Evaluation Engine error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Stage 8 Opportunity Evaluation Engine Health Check"
)
async def get_opportunity_engine_health():
    return {
        "engine": "deterministic_opportunity_evaluation_engine",
        "stage": 8,
        "status": "healthy",
        "weights": OPPORTUNITY_WEIGHTS,
        "version": opportunity_evaluation_engine.version
    }
