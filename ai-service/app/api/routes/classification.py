import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models.intake import IntakeSession
from app.schemas.classification import (
    BusinessClassificationRequest,
    ClassificationResult,
    ClarifyClassificationRequest
)
from app.services.classification.classification_service import run_business_classification
from app.services.classification.nic_service import get_nic_by_code
from app.core.logging import logger

router = APIRouter(prefix="/classification", tags=["Classification"])


@router.post("/classify", response_model=ClassificationResult, status_code=status.HTTP_200_OK)
async def classify_business(
    payload: BusinessClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Stage 2 Business Classification Engine:
    Processes verified Stage 1 intake JSON and produces validated Layer A (NIC) + Layer B (Ontology) classification.
    """
    logger.info(f"[API CLASSIFY] Received classification request: session_id={payload.session_id}")
    
    # If session_id provided but no explicit fields, attempt to load from database
    payload_dict = payload.model_dump()
    session_id = payload.session_id or payload.intake_id
    
    if session_id and not payload.business_concept and not payload.original_input and not payload.original_text:
        try:
            intake_uuid = uuid.UUID(session_id)
            intake_sess = db.query(IntakeSession).filter(IntakeSession.id == intake_uuid).first()
            if intake_sess and intake_sess.structured_profile:
                payload_dict = intake_sess.structured_profile
                payload_dict["session_id"] = session_id
                logger.info(f"[API CLASSIFY] Loaded Stage 1 profile from database for session_id={session_id}")
        except Exception as e:
            logger.warning(f"[API CLASSIFY] Could not load intake session from DB: {e}")

    result = await run_business_classification(payload_dict, db=db)
    return result


@router.post("/clarify", response_model=ClassificationResult, status_code=status.HTTP_200_OK)
async def clarify_business_classification(
    payload: ClarifyClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Re-runs classification with clarification answer provided by the user.
    """
    logger.info(f"[API CLARIFY] Clarifying session_id={payload.session_id} with answer='{payload.answer}'")
    
    base_payload = {
        "session_id": payload.session_id,
        "original_input": payload.answer,
        "business_concept": payload.answer,
        "language_code": payload.language_code
    }
    
    # Merge existing session profile if available
    try:
        intake_uuid = uuid.UUID(payload.session_id)
        intake_sess = db.query(IntakeSession).filter(IntakeSession.id == intake_uuid).first()
        if intake_sess and intake_sess.structured_profile:
            merged = dict(intake_sess.structured_profile)
            merged["business_concept"] = payload.answer
            merged["original_input"] = f"{merged.get('original_input', '')} - {payload.answer}".strip(" -")
            base_payload = merged
            base_payload["session_id"] = payload.session_id
    except Exception as e:
        logger.warning(f"[API CLARIFY] Error loading session context: {e}")

    result = await run_business_classification(base_payload, db=db)
    return result


@router.get("/{session_id}", response_model=ClassificationResult, status_code=status.HTTP_200_OK)
async def get_classification_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the latest classification status for a given session.
    """
    try:
        intake_uuid = uuid.UUID(session_id)
        intake_sess = db.query(IntakeSession).filter(IntakeSession.id == intake_uuid).first()
        if not intake_sess:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
        prof = intake_sess.structured_profile or {}
        if "stage_2_classification" in prof:
            return prof["stage_2_classification"]
        
        # Run classification if not yet classified
        result = await run_business_classification(prof, db=db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API GET CLASSIFICATION] Error retrieving session {session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/nic/{code}", status_code=status.HTTP_200_OK)
async def get_nic_code_details(code: str):
    """
    Retrieves full NIC 2008 details for a given code.
    """
    nic_record = get_nic_by_code(code)
    if not nic_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"NIC code {code} not found in official dataset")
    return nic_record
