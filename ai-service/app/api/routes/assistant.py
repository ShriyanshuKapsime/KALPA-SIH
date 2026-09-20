"""
FastAPI Route for Stage 15: KALPA Personal AI Business Assistant.
Exposes endpoints for chat, history retrieval, context inspection, and history clearing.
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.database.session import get_db
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHistoryResponse,
    AssistantContextResponse,
    ConversationHistoryItem,
    AssistantSTTResponse,
    AssistantTTSRequest,
    AssistantTTSResponse
)
from app.services.assistant_engine.assistant_service import assistant_service
from app.services.assistant_engine.context_builder import (
    build_full_assistant_context,
    calculate_pipeline_completeness,
    safe_uuid
)
from app.services.sarvam_service import sarvam_stt_service, sarvam_tts_service

router = APIRouter(prefix="/assistant", tags=["Stage 15 — Personal AI Business Assistant"])


@router.get(
    "/health",
    summary="Stage 15 Assistant Health Check",
    description="Lightweight health check confirming router availability without invoking LLM inference."
)
async def assistant_health():
    return {"status": "ok", "service": "stage15-assistant"}


@router.post(
    "/stt",
    response_model=AssistantSTTResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio message via Sarvam Saaras STT (saaras:v4)",
    description="Accepts recorded audio from user microphone, runs Sarvam STT in user's language, returns transcribed text."
)
async def assistant_speech_to_text(
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    language: Optional[str] = Form(None)
):
    upload = file or audio
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file payload is required."
        )

    try:
        audio_bytes = await upload.read()
        if not audio_bytes or len(audio_bytes) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty or invalid audio stream received."
            )

        transcript, detected_lang = await sarvam_stt_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=upload.filename or "recording.webm",
            content_type=upload.content_type or "audio/webm",
            language_code=language
        )

        return AssistantSTTResponse(
            success=True,
            text=transcript,
            language=language or detected_lang or "en",
            detected_language=detected_lang
        )
    except ValueError as ve:
        logger.warning(f"[ASSISTANT STT] Config error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice input service is currently unconfigured. Please type your message."
        )
    except Exception as e:
        logger.error(f"[ASSISTANT STT ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice input couldn't be understood. Please try again or type your question."
        )


@router.post(
    "/tts",
    response_model=AssistantTTSResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize speech audio via Sarvam Bulbul TTS (bulbul:v3)",
    description="Accepts assistant text response, cleans markdown/metadata, and returns base64 playable audio."
)
async def assistant_text_to_speech(
    request: AssistantTTSRequest
):
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required for speech synthesis."
        )

    try:
        res = await sarvam_tts_service.synthesize_speech(
            text=request.text,
            language_code=request.language or "hi",
            speaker=request.speaker
        )
        return AssistantTTSResponse(**res)
    except ValueError as ve:
        logger.warning(f"[ASSISTANT TTS] Config error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice playback isn't available right now. You can still read the answer."
        )
    except Exception as e:
        logger.error(f"[ASSISTANT TTS ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice playback isn't available right now. You can still read the answer."
        )


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to Personal AI Business Assistant",
    description="Processes user query, detects intent, retrieves canonical business context, and queries Sarvam LLM."
)
async def chat_with_assistant(
    request: AssistantChatRequest,
    db: Session = Depends(get_db)
):
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    analysis_uuid = safe_uuid(request.analysis_id)
    session_uuid = safe_uuid(request.session_id)
    if not analysis_uuid and not session_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a valid analysis_id or session_id must be provided."
        )

    try:
        res = await assistant_service.handle_message(
            user_message=request.message,
            db=db,
            analysis_id_str=request.analysis_id,
            session_id_str=request.session_id,
            conversation_id_str=request.conversation_id,
            business_id_str=request.business_id,
            language=request.language or "en"
        )
        return AssistantChatResponse(**res)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"[ASSISTANT ROUTE] Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KALPA couldn't process that question right now. Please try again."
        )


@router.get(
    "/{analysis_id}/history",
    response_model=AssistantHistoryResponse,
    summary="Get conversation history for an analysis ID"
)
@router.get(
    "/history/{target_id}",
    response_model=AssistantHistoryResponse,
    summary="Get conversation history for an analysis/session ID",
    include_in_schema=False
)
async def get_assistant_history(
    analysis_id: Optional[str] = None,
    target_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    effective_id = analysis_id or target_id
    target_uuid = safe_uuid(effective_id)
    if not target_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for analysis or session ID"
        )

    try:
        history = assistant_service.get_history(effective_id, db)
        items = [ConversationHistoryItem(**h) for h in history]
        return AssistantHistoryResponse(target_id=effective_id, messages=items)
    except Exception as e:
        logger.error(f"[ASSISTANT ROUTE] History error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve history: {str(e)}"
        )


@router.get(
    "/{analysis_id}/context",
    response_model=AssistantContextResponse,
    summary="Get full grounded business context loaded for the assistant"
)
@router.get(
    "/context/{target_id}",
    response_model=AssistantContextResponse,
    summary="Get full grounded business context for an analysis/session ID",
    include_in_schema=False
)
async def get_assistant_context(
    analysis_id: Optional[str] = None,
    target_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    effective_id = analysis_id or target_id
    target_uuid = safe_uuid(effective_id)
    if not target_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for analysis or session ID"
        )

    try:
        ctx = build_full_assistant_context(
            analysis_id=effective_id,
            session_id=effective_id,
            db=db
        )
        completeness = calculate_pipeline_completeness(ctx)
        return AssistantContextResponse(
            analysis_id=effective_id,
            session_id=effective_id,
            pipeline_completeness=completeness,
            context=ctx
        )
    except Exception as e:
        logger.error(f"[ASSISTANT ROUTE] Context retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve context: {str(e)}"
        )


@router.delete(
    "/{analysis_id}/history",
    summary="Clear conversation history for an analysis ID"
)
@router.delete(
    "/history/{target_id}",
    summary="Clear conversation history for an analysis/session ID",
    include_in_schema=False
)
async def clear_assistant_history(
    analysis_id: Optional[str] = None,
    target_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    effective_id = analysis_id or target_id
    target_uuid = safe_uuid(effective_id)
    if not target_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for analysis or session ID"
        )

    try:
        success = assistant_service.clear_history(effective_id, db)
        return {"success": success, "message": "History cleared"}
    except Exception as e:
        logger.error(f"[ASSISTANT ROUTE] History clear error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not clear history: {str(e)}"
        )


logger.info("[ASSISTANT ROUTER] POST /api/v1/assistant/chat registered")
logger.info("[ASSISTANT ROUTER] POST /api/v1/assistant/stt registered")
logger.info("[ASSISTANT ROUTER] POST /api/v1/assistant/tts registered")
logger.info("[ASSISTANT ROUTER] GET /api/v1/assistant/{analysis_id}/history registered")
logger.info("[ASSISTANT ROUTER] GET /api/v1/assistant/{analysis_id}/context registered")
logger.info("[ASSISTANT ROUTER] GET /api/v1/assistant/health registered")

