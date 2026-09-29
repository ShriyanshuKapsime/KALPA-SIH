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
    file: Optional[UploadFile] = File(None, description="Audio recording file (wav, webm, mp3, etc.)"),
    audio: Optional[UploadFile] = File(None, description="Alternative field name for audio file"),
    transcript: Optional[str] = Form(None, description="Client or browser-side recognized transcript"),
    language_code: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    selected_language: Optional[str] = Form(None),
    db: Optional[Session] = Depends(get_db)
):
    """
    Accepts audio recording or pre-transcribed voice text in English, Kannada, Hindi or Indic languages,
    transcribes using Sarvam Saaras STT (or client recognition), and executes Stage 1 NLP extraction.
    """
    logger.info("[AI INTAKE ROUTE HIT] POST /api/v1/intake/voice")
    resolved_transcript = (transcript or "").strip()
    detected_lang = None

    try:
        # 1. If transcript already provided by client (e.g. browser Web Speech API), use it directly
        if resolved_transcript:
            logger.info(f"[VOICE INTAKE] Using client-provided transcript: '{resolved_transcript[:60]}...'")
        else:
            upload = file or audio
            if not upload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either an audio file or a transcript text must be provided."
                )

            audio_bytes = await upload.read()
            if not audio_bytes or len(audio_bytes) < 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded audio file is empty or corrupted."
                )

            # Transcribe with Sarvam Saaras STT
            try:
                resolved_transcript, detected_lang = await sarvam_stt_service.transcribe_audio(
                    audio_bytes=audio_bytes,
                    filename=upload.filename or "recording.webm",
                    content_type=upload.content_type or "audio/webm",
                    language_code=language_code
                )
            except Exception as stt_err:
                logger.warning(f"[VOICE INTAKE] Sarvam STT failed: {stt_err}")
                err_str = str(stt_err)
                if "402" in err_str or "credit" in err_str.lower() or "quota" in err_str.lower():
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={
                            "success": False,
                            "error": "STT_QUOTA_EXCEEDED",
                            "message": "Voice recognition service quota depleted. Please enter your business idea as text.",
                            "details": {"provider_error": err_str}
                        }
                    )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "success": False,
                        "error": "STT_PROCESSING_FAILED",
                        "message": "Voice recognition provider is temporarily unavailable. Please enter your business idea as text.",
                        "details": {"provider_error": err_str}
                    }
                )

        if not resolved_transcript or not isinstance(resolved_transcript, str) or not resolved_transcript.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not detect clear speech in the recording. Please try speaking closer to the microphone or use text input."
            )
        resolved_transcript = resolved_transcript.strip()

        # 2. Process Transcript through Stage 1 NLP pipeline
        active_lang = selected_language or detected_lang or language_code
        stage1_resp = await process_user_intake(
            text=resolved_transcript,
            input_type="voice",
            language_override=detected_lang or language_code,
            user_id=user_id,
            selected_language=active_lang,
            db=db
        )

        return VoiceIntakeResponse(
            success=True,
            transcript=resolved_transcript,
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
    except Exception as e:
        logger.error(f"Unexpected error in voice intake: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "STT_INTERNAL_ERROR",
                "message": "Voice processing is temporarily unavailable. Please enter your idea as text.",
                "details": str(e)
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


@router.post("/transcribe", status_code=status.HTTP_200_OK)
async def transcribe_voice(
    file: Optional[UploadFile] = File(None, description="Audio recording file (wav, webm, mp3, etc.)"),
    audio: Optional[UploadFile] = File(None, description="Alternative field name for audio file"),
    transcript: Optional[str] = Form(None, description="Client or browser-side recognized transcript"),
    language_code: Optional[str] = Form(None),
):
    """
    Direct Speech-to-Text transcription via Sarvam Saaras STT (or client recognition) without triggering Stage 1 full intake.
    Used for clarification questions, voice responses, and multilingual input across all stages.
    """
    logger.info("[AI INTAKE ROUTE HIT] POST /api/v1/intake/transcribe")
    stt_model = getattr(sarvam_stt_service, "model", "saaras:v4")
    detected_lang = language_code or "unknown"

    try:
        # 1. If client already supplied a valid text transcript, normalize and return immediately
        client_transcript = transcript.strip() if (transcript is not None and isinstance(transcript, str)) else None
        if client_transcript:
            logger.info(f"[VOICE TRANSCRIBE] Using client-provided transcript: '{client_transcript[:60]}...'")
            return {
                "success": True,
                "transcript": client_transcript,
                "provider": "client",
                "model": "client",
                "language": detected_lang,
                "error": None
            }

        # 2. Check for uploaded audio file
        upload = file or audio
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "transcript": None,
                    "provider": "sarvam",
                    "model": stt_model,
                    "error": {
                        "code": "MISSING_AUDIO",
                        "message": "Either an audio file or a transcript text must be provided."
                    }
                }
            )

        audio_bytes = await upload.read()
        upload_filename = upload.filename or "recording.webm"
        upload_content_type = upload.content_type or "audio/webm"
        byte_size = len(audio_bytes) if audio_bytes else 0

        # Safe logging conforming to spec
        logger.info(
            f"STT request received: filename='{upload_filename}', content_type='{upload_content_type}', byte_size={byte_size}"
        )
        logger.info(
            f"STT provider: provider='sarvam', model='{stt_model}'"
        )

        if not audio_bytes or byte_size < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "transcript": None,
                    "provider": "sarvam",
                    "model": stt_model,
                    "error": {
                        "code": "EMPTY_OR_CORRUPT_AUDIO",
                        "message": "Uploaded audio file is empty or corrupted."
                    }
                }
            )

        # 3. Call Sarvam STT service
        try:
            resolved_transcript, detected_lang = await sarvam_stt_service.transcribe_audio(
                audio_bytes=audio_bytes,
                filename=upload_filename,
                content_type=upload_content_type,
                language_code=language_code
            )
        except ValueError as cfg_err:
            logger.warning(f"Voice transcribe configuration error: {cfg_err}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "success": False,
                    "transcript": None,
                    "provider": "sarvam",
                    "model": stt_model,
                    "error": {
                        "code": "STT_CONFIG_ERROR",
                        "message": str(cfg_err)
                    }
                }
            )
        except Exception as stt_err:
            logger.warning(f"[VOICE TRANSCRIBE] Sarvam STT failed: {stt_err}")
            err_str = str(stt_err)
            is_quota = "402" in err_str or "credit" in err_str.lower() or "quota" in err_str.lower()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "success": False,
                    "transcript": None,
                    "provider": "sarvam",
                    "model": stt_model,
                    "error": {
                        "code": "STT_QUOTA_EXCEEDED" if is_quota else "STT_PROVIDER_ERROR",
                        "message": "Voice recognition service quota depleted. Please enter your text response." if is_quota else f"Sarvam STT provider error: {err_str}"
                    }
                }
            )

        # 4. Explicit validation: Never call .strip() before checking that transcript is a string
        if resolved_transcript is None or not isinstance(resolved_transcript, str):
            clean_transcript = ""
        else:
            clean_transcript = resolved_transcript.strip()

        if not clean_transcript:
            return {
                "success": False,
                "transcript": "",
                "provider": "sarvam",
                "model": stt_model,
                "language": detected_lang or language_code or "unknown",
                "error": {
                    "code": "STT_NO_SPEECH_DETECTED",
                    "message": "Could not detect clear speech in the recording. Please speak closer to the mic or type your answer."
                }
            }

        # 5. Canonical Success Response
        return {
            "success": True,
            "transcript": clean_transcript,
            "provider": "sarvam",
            "model": stt_model,
            "language": detected_lang or language_code or "unknown",
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice transcribe unexpected internal error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "transcript": None,
                "provider": "sarvam",
                "model": stt_model,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Unexpected internal error during voice transcription: {str(e)}"
                }
            }
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
