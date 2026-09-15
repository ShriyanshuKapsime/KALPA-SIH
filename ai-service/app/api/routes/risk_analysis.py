"""
Risk Analysis API Router (Stage 11).
Exposes REST endpoints for deterministic multi-vector risk evaluation and health checks.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.schemas.risk_analysis import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
)
from app.services.risk_engine import (
    risk_engine,
)
from app.database.session import get_db
from app.core.logging import logger

router = APIRouter(prefix="/risk-analysis", tags=["Stage 11 — Risk Engine"])


@router.post(
    "/analyze",
    response_model=RiskAnalysisResponse,
    summary="Stage 11 Deterministic Risk Engine",
    description="Evaluates Market, Financial, Operational, Seasonal, Supply Chain, Competition, and Infrastructure risks with critical risk preservation."
)
async def analyze_enterprise_risks(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    logger.info("[API STAGE 11] Received enterprise risk analysis request")
    try:
        result = risk_engine.analyze(payload)
        return result
    except Exception as e:
        logger.error(f"[API STAGE 11 ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 11 Risk Engine error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Stage 11 Risk Engine Health Check"
)
async def get_risk_engine_health():
    return {
        "engine": "deterministic_risk_engine",
        "stage": 11,
        "status": "healthy",
        "evaluation_mode": "DETERMINISTIC_MULTI_VECTOR_SYNTHESIS",
        "categories": [
            "MARKET",
            "FINANCIAL",
            "OPERATIONAL",
            "SEASONAL",
            "SUPPLY_CHAIN",
            "COMPETITION",
            "INFRASTRUCTURE"
        ],
        "critical_ceiling_rule": "ENABLED",
        "version": "1.0.0"
    }
