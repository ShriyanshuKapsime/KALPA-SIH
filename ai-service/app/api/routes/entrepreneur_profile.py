"""
Entrepreneur Profile API Router (Stage 10).
Exposes REST endpoints for deterministic entrepreneur readiness evaluation,
contextual clarification extraction, canonical profile merging, DB persistence, and health status.
"""
from typing import Dict, Any, Optional
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Body
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

# Module-level cache for sessions/analysis where DB record is transient or mock
_transient_profile_cache: Dict[str, Dict[str, Any]] = {}


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
        session_id = payload.get("session_id")

        # Enrich from DB if available
        if (analysis_id or session_id) and not payload.get("business_profile"):
            try:
                rec = None
                if analysis_id:
                    try:
                        rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.id == uuid.UUID(analysis_id)
                        ).first()
                    except Exception:
                        pass
                if not rec and session_id:
                    try:
                        rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.session_id == uuid.UUID(session_id)
                        ).order_by(StructuredBusinessProfile.created_at.desc()).first()
                    except Exception:
                        pass

                if rec and rec.profile_json:
                    p_json = rec.profile_json
                    payload["business_profile"] = payload.get("business_profile") or p_json.get("business_profile")
                    payload["location_profile"] = payload.get("location_profile") or p_json.get("location_profile")
                    payload["financial_profile"] = payload.get("financial_profile") or p_json.get("financial_profile")
                    if not payload.get("entrepreneur_profile") and not payload.get("user_profile"):
                        payload["entrepreneur_profile"] = p_json.get("entrepreneur_profile") or p_json.get("user_profile")
            except Exception as e:
                logger.warning(f"[API STAGE 10] DB lookup note: {e}")

        if not payload.get("entrepreneur_profile") and not payload.get("user_profile"):
            if analysis_id and str(analysis_id) in _transient_profile_cache:
                payload["entrepreneur_profile"] = _transient_profile_cache[str(analysis_id)]
            elif session_id and str(session_id) in _transient_profile_cache:
                payload["entrepreneur_profile"] = _transient_profile_cache[str(session_id)]

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
    summary="Clarification Extractor & Profile Re-evaluator",
    description="Contextually extracts structured profile facts, merges into canonical profile, persists to DB, and re-evaluates Stage 10."
)
async def clarify_entrepreneur_profile(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submits a clarification (text or speech transcript) against a specific pending question/field.
    Persists answered facts into the canonical profile, updates answered_fields tracking,
    and returns the re-calculated readiness evaluation.
    """
    analysis_id = payload.get("analysis_id")
    session_id = payload.get("session_id")
    field = payload.get("field") or payload.get("question_id")
    text = payload.get("text") or payload.get("transcript") or payload.get("answer")
    language = payload.get("language", "hi")
    is_voice = payload.get("is_voice", False)

    if not text or not str(text).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clarification text/answer cannot be empty."
        )

    logger.info(f"[API STAGE 10 CLARIFY] field='{field}', text='{text[:60]}', is_voice={is_voice}")

    try:
        # 1. Fetch existing profile from DB if available
        rec = None
        current_ep = payload.get("entrepreneur_profile") or payload.get("user_profile") or {}
        business_profile = payload.get("business_profile") or {}
        location_profile = payload.get("location_profile") or {}
        financial_profile = payload.get("financial_profile") or {}

        if not current_ep and analysis_id and analysis_id in _transient_profile_cache:
            current_ep = _transient_profile_cache[analysis_id]
        if not current_ep and session_id and session_id in _transient_profile_cache:
            current_ep = _transient_profile_cache[session_id]

        if analysis_id or session_id:
            try:
                if analysis_id:
                    try:
                        rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.id == uuid.UUID(analysis_id)
                        ).first()
                    except Exception:
                        pass
                if not rec and session_id:
                    try:
                        rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.session_id == uuid.UUID(session_id)
                        ).order_by(StructuredBusinessProfile.created_at.desc()).first()
                    except Exception:
                        pass

                if rec and rec.profile_json:
                    p_json = rec.profile_json
                    business_profile = business_profile or p_json.get("business_profile") or {}
                    location_profile = location_profile or p_json.get("location_profile") or {}
                    financial_profile = financial_profile or p_json.get("financial_profile") or {}
                    if not current_ep:
                        current_ep = p_json.get("entrepreneur_profile") or p_json.get("user_profile") or {}
            except Exception as e:
                logger.warning(f"[API STAGE 10 CLARIFY] DB lookup warning: {e}")

        # 2. Contextual deterministic extraction
        extracted = await clarification_extractor.extract_with_optional_llm(
            text=str(text),
            field_hint=field,
            business_context=business_profile,
            language=language,
            is_voice=is_voice
        )

        # 3. Merge into canonical entrepreneur profile and record answered field
        updated_ep = entrepreneur_profile_engine.merge_profiles(current_ep, extracted)
        if field:
            answered_set = set(updated_ep.get("answered_fields", []))
            answered_set.add(field)
            if "." in field:
                answered_set.add(field.split(".")[0])
            updated_ep["answered_fields"] = sorted(list(answered_set))

        # Cache in transient memory for session persistence
        if analysis_id:
            _transient_profile_cache[str(analysis_id)] = updated_ep
        if session_id:
            _transient_profile_cache[str(session_id)] = updated_ep

        # 4. Persist updated canonical profile in PostgreSQL if record exists
        if rec and rec.profile_json:
            try:
                p_json = dict(rec.profile_json)
                p_json["entrepreneur_profile"] = updated_ep
                p_json["user_profile"] = updated_ep
                rec.profile_json = p_json
                db.commit()
                db.refresh(rec)
                logger.info(f"[API STAGE 10 CLARIFY] Successfully persisted updated entrepreneur profile to DB (id={rec.id})")
            except Exception as db_err:
                logger.warning(f"[API STAGE 10 CLARIFY] DB persist warning: {db_err}")
                db.rollback()

        # 5. Re-run Stage 10 Evaluation with updated canonical profile
        eval_payload = {
            "analysis_id": analysis_id or (str(rec.id) if rec else None),
            "session_id": session_id or (str(rec.session_id) if rec else None),
            "business_profile": business_profile,
            "location_profile": location_profile,
            "financial_profile": financial_profile,
            "entrepreneur_profile": updated_ep
        }
        readiness_resp = entrepreneur_profile_engine.analyze(eval_payload)

        # Validate that every question has question text
        for q in readiness_resp.questions:
            if not q.question:
                logger.warning(f"[API STAGE 10 VALIDATION WARNING] Question for field '{q.field}' has empty question text: {q}")

        return {
            "success": True,
            "analysis_id": analysis_id,
            "session_id": session_id,
            "target_field": field,
            "raw_text": text,
            "extracted_facts": extracted,
            "entrepreneur_profile": updated_ep,
            "readiness_response": readiness_resp.model_dump(),
            "readiness_evaluation": readiness_resp.model_dump(),
            # Top level convenience attributes for frontend consumption
            "component_scores": readiness_resp.component_scores,
            "readiness_score": readiness_resp.readiness_score,
            "readiness_level": readiness_resp.readiness_level,
            "overall_score": readiness_resp.overall_score,
            "level": readiness_resp.level,
            "weights": readiness_resp.weights,
            "calculation_provenance": readiness_resp.calculation_provenance,
            "pending_fields": readiness_resp.pending_fields,
            "answered_fields": readiness_resp.answered_fields,
            "missing_fields": readiness_resp.missing_fields,
            "pending_count": len(readiness_resp.questions),
            "questions": [q.model_dump() for q in readiness_resp.questions],
            "status": readiness_resp.status,
            "strengths": readiness_resp.strengths,
            "gaps": [g.model_dump() for g in readiness_resp.gaps],
            "required_support": [s.model_dump() for s in readiness_resp.required_support],
            "confidence": readiness_resp.confidence
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API STAGE 10 CLARIFY ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clarification processing error: {str(e)}"
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
        "version": "1.1.0"
    }
