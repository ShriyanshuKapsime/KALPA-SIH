import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.intake import IntakeSession
from app.schemas.intake import (
    TextInputRequest,
    ContinueIntakeRequest,
    Stage1IntakeResponse,
    VoiceIntakeResponse,
)
from app.services.intake_pipeline import process_user_intake, continue_user_intake, get_cached_or_db_session
from app.services.sarvam_service import sarvam_stt_service
from app.core.logging import logger

router = APIRouter(prefix="/intake", tags=["Intake"])


@router.post("/text", response_model=Stage1IntakeResponse, status_code=status.HTTP_200_OK)
async def submit_text_intake(
    payload: TextInputRequest,
    db: Optional[Session] = Depends(get_db)
):
    """
    Process English, Kannada, Hindi, or vernacular text through the Stage 1 NLP intake pipeline.
    """
    logger.info(f"[AI INTAKE ROUTE HIT] POST /api/v1/intake/text: {payload.text[:60] if payload.text else ''}")
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Intake text cannot be empty."
        )

    try:
        response = await process_user_intake(
            text=payload.text,
            input_type="text",
            language_override=payload.language_code,
            user_id=payload.user_id,
            selected_language=payload.selected_language,
            db=db
        )
        return response
    except Exception as e:
        logger.error(f"Error in text intake processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process business intake. Please try again."
        )


@router.post("/voice", response_model=VoiceIntakeResponse, status_code=status.HTTP_200_OK)
async def submit_voice_intake(
    file: UploadFile = File(..., description="Audio recording file (wav, webm, mp3, etc.)"),
    language_code: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    selected_language: Optional[str] = Form(None),
    db: Optional[Session] = Depends(get_db)
):
    """
    Accepts audio recording in English, Kannada, Hindi or Indic languages, transcribes using Sarvam Saaras STT,
    and executes Stage 1 NLP extraction.
    """
    logger.info("[AI INTAKE ROUTE HIT] POST /api/v1/intake/voice")
    try:
        audio_bytes = await file.read()
        if not audio_bytes or len(audio_bytes) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio file is empty or corrupted."
            )

        # 1. Transcribe with Sarvam Saaras STT
        transcript, detected_lang = await sarvam_stt_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.wav",
            content_type=file.content_type or "audio/wav",
            language_code=language_code
        )

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not detect clear speech in the recording. Please try speaking closer to the microphone or use text input."
            )

        # 2. Process Transcript through Stage 1 NLP pipeline
        active_lang = selected_language or detected_lang or language_code
        stage1_resp = await process_user_intake(
            text=transcript,
            input_type="voice",
            language_override=detected_lang or language_code,
            user_id=user_id,
            selected_language=active_lang,
            db=db
        )

        return VoiceIntakeResponse(
            success=True,
            transcript=transcript,
            session_id=stage1_resp.session_id,
            language=stage1_resp.language,
            profile=stage1_resp.profile,
            missing_fields=stage1_resp.missing_fields,
            next_action=stage1_resp.next_action
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Voice intake configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "error": "STT_CONFIG_ERROR",
                "message": str(e),
                "details": {"received_language": language_code or "unknown"}
            }
        )
    except RuntimeError as e:
        logger.error(f"Voice intake runtime failure: {e}")
        is_400 = "400" in str(e) or "rejected" in str(e).lower()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if is_400 else status.HTTP_502_BAD_GATEWAY,
            detail={
                "success": False,
                "error": "STT_LANGUAGE_CODE_INVALID" if "language_code" in str(e) else "STT_PROCESSING_FAILED",
                "message": "Voice recognition configuration failed" if is_400 else "Voice processing provider temporarily unreachable",
                "details": {
                    "provider_error": str(e),
                    "received_language": language_code or "unknown"
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in voice intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "STT_INTERNAL_ERROR",
                "message": "Voice processing is temporarily unavailable. Please try again or enter your idea as text.",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.post("/continue", response_model=Stage1IntakeResponse, status_code=status.HTTP_200_OK)
async def continue_intake(
    payload: ContinueIntakeRequest,
    db: Optional[Session] = Depends(get_db)
):
    """
    Submits follow-up answers (text, voice transcript, structured answers, or GPS) to merge into existing Stage 1 session.
    """
    target_session_id = payload.session_id or payload.intake_id
    if not target_session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="session_id or intake_id is required."
        )

    logger.info(f"[AI INTAKE ROUTE HIT] POST /api/v1/intake/continue for session {target_session_id}")
    try:
        response = await continue_user_intake(
            session_id=target_session_id,
            answers=payload.answers,
            follow_up_text=payload.text,
            field=payload.field,
            language_code=payload.language_code,
            gps_location=payload.gps_location,
            db=db
        )
        return response
    except Exception as e:
        logger.error(f"Error continuing intake session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update intake profile with new answers."
        )


@router.get("/session/{session_id}", response_model=Stage1IntakeResponse, status_code=status.HTTP_200_OK)
async def get_intake_session(
    session_id: str,
    db: Optional[Session] = Depends(get_db)
):
    """
    Retrieve stored Stage 1 intake session profile by session ID.
    """
    resp = get_cached_or_db_session(session_id, db=db)
    if not resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intake session {session_id} not found."
        )
    return resp
