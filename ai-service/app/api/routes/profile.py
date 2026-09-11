from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.profile import BuildProfileRequest, BuildProfileResponse, CanonicalBusinessProfile
from app.services.profile_service import (
    build_canonical_profile_for_session,
    get_profile_by_analysis_id,
    get_profile_by_session_id
)
from app.core.logging import logger

router = APIRouter(prefix="/profile", tags=["Profile Store"])


@router.post("/build", response_model=BuildProfileResponse, status_code=status.HTTP_200_OK)
async def build_profile(
    payload: BuildProfileRequest,
    db: Session = Depends(get_db)
):
    """
    Stage 3 Profile Builder Endpoint:
    Merges Stage 1 Intake + Stage 2 Classification into the canonical Structured Business Profile,
    validates data consistency, attaches ontology analysis requirements, and persists to PostgreSQL.
    """
    logger.info(f"[API PROFILE BUILD] Received request for session_id={payload.session_id}")
    try:
        canonical_profile = await build_canonical_profile_for_session(payload.session_id, db=db)
        return {
            "success": True,
            "analysis_id": canonical_profile["analysis_id"],
            "session_id": canonical_profile["session_id"],
            "workflow_state": canonical_profile["workflow"]["state"],
            "profile": canonical_profile
        }
    except ValueError as ve:
        logger.warning(f"[API PROFILE BUILD NOT FOUND] {ve}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"[API PROFILE BUILD ERROR] {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to build business profile: {e}")


@router.get("/{analysis_id}", response_model=CanonicalBusinessProfile, status_code=status.HTTP_200_OK)
async def get_profile_by_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves canonical business profile by analysis_id.
    """
    profile = get_profile_by_analysis_id(analysis_id, db=db)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business profile with analysis_id {analysis_id} not found")
    return profile


@router.get("/session/{session_id}", response_model=CanonicalBusinessProfile, status_code=status.HTTP_200_OK)
async def get_profile_by_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves canonical business profile by session_id.
    """
    profile = get_profile_by_session_id(session_id, db=db)
    if not profile:
        # If not built yet, attempt to build on the fly
        try:
            profile = await build_canonical_profile_for_session(session_id, db=db)
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No business profile found for session {session_id}")
    return profile
