"""
Financial Analysis API Router (Stage 9).
Exposes REST endpoints for deterministic project financing, scheme routing,
loan management, amortization, profitability projections, and standalone loan calculator.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialCalculatorRequest,
    FinancialCalculatorResponse
)
from app.services.financial_engine import financial_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-analysis", tags=["Stage 9: Financial Engine"])


@router.post("/analyze", response_model=FinancialAnalysisResponse)
async def analyze_financial_profile(payload: FinancialAnalysisRequest):
    """
    Executes deterministic Stage 9 financial analysis for an active MSME profile.
    Calculates project financing, scheme routing, capital allocation, loan management,
    amortization schedule, profitability, cash flows, break-even, DSCR, and financial viability.
    """
    try:
        logger.info(
            f"[API STAGE 9] Received financial analysis request: "
            f"analysis_id={payload.analysis_id}, session_id={payload.session_id}, "
            f"margin_capital={payload.financial_profile.available_margin_capital}"
        )
        response = financial_engine.analyze(payload)
        return response
    except Exception as e:
        logger.error(f"[API STAGE 9] Error during financial evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Financial evaluation failed: {str(e)}"
        )


@router.post("/calculator", response_model=FinancialCalculatorResponse)
async def calculate_loan_and_scheme(payload: FinancialCalculatorRequest):
    """
    Standalone interactive loan and margin calculator endpoint.
    Supports margin-to-loan, cost-to-margin, and loan-to-EMI calculation modes.
    """
    try:
        logger.info(f"[API STAGE 9] Received standalone calculator request: {payload}")
        response = financial_engine.calculate(payload)
        return response
    except Exception as e:
        logger.error(f"[API STAGE 9] Error during standalone calculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Financial calculation failed: {str(e)}"
        )


@router.get("/health")
async def get_financial_engine_health():
    """
    Returns the operational status and capabilities of the Deterministic Financial Engine.
    """
    return financial_engine.health()
