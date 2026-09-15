"""
Entrepreneur Profile API Router (Stage 10).
Exposes REST endpoints for deterministic entrepreneur readiness evaluation,
targeted clarification handling, and health status.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
)
from app.services.entrepreneur_profile_engine import (
    entrepreneur_profile_engine,
    clarification_extractor,
)
from app.database.session import get_db
from app.database.models.profile import StructuredBusinessProfile
from app.core.logging import logger

router = APIRouter(prefix="/entrepreneur-profile", tags=["Stage 10 — Entrepreneur Profile Engine"])


@router.post(
    "/analyze",
    response_model=EntrepreneurReadinessResponse,
    summary="Stage 10 Deterministic Entrepreneur Profile Engine",
    description="Evaluates entrepreneur ↔ business alignment across Skills, Experience, Training, Resources, and Operational readiness."
)
async def analyze_entrepreneur_profile(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    logger.info("[API STAGE 10] Received entrepreneur profile evaluation request")
    try:
        analysis_id = payload.get("analysis_id")

        # If payload only has analysis_id, enrich from DB if available
        if analysis_id and not payload.get("business_profile"):
            try:
                rec = db.query(StructuredBusinessProfile).filter(StructuredBusinessProfile.id == analysis_id).first()
                if rec and rec.profile_json:
                    payload["business_profile"] = rec.profile_json.get("business_profile")
                    payload["location_profile"] = rec.profile_json.get("location_profile")
                    payload["financial_profile"] = rec.profile_json.get("financial_profile")
                    if not payload.get("entrepreneur_profile"):
                        payload["entrepreneur_profile"] = rec.profile_json.get("entrepreneur_profile") or rec.profile_json.get("user_profile")
            except Exception as e:
                logger.warning(f"[API STAGE 10] DB lookup note: {e}")

        result = entrepreneur_profile_engine.analyze(payload)
        return result
    except Exception as e:
        logger.error(f"[API STAGE 10 ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 10 Entrepreneur Profile Engine error: {str(e)}"
        )


@router.post(
    "/clarify",
    summary="Clarification Extractor (Voice/Text to Structured Facts)",
    description="Extracts structured profile facts from user answer without calculating readiness scores."
)
async def clarify_entrepreneur_profile(
    payload: Dict[str, Any]
):
    text = payload.get("text") or payload.get("answer") or ""
    field = payload.get("field")
    try:
        extracted = await clarification_extractor.extract_with_optional_llm(text, field_hint=field)
        return {
            "success": True,
            "raw_text": text,
            "target_field": field,
            "extracted_facts": extracted
        }
    except Exception as e:
        logger.error(f"[API STAGE 10 CLARIFY ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clarification extraction error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Stage 10 Entrepreneur Profile Engine Health Check"
)
async def get_entrepreneur_engine_health():
    return {
        "engine": "deterministic_entrepreneur_profile_engine",
        "stage": 10,
        "status": "healthy",
        "evaluation_mode": "DETERMINISTIC_RULES",
        "dimensions": [
            "skill_alignment",
            "experience_alignment",
            "training_readiness",
            "resource_availability",
            "operational_readiness"
        ],
        "version": "1.0.0"
    }
