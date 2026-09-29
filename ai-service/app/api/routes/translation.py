"""
FastAPI Routes for Stage 16: KALPA Multilingual Translation Engine.
Exposes REST endpoints for translating text, batch arrays, and nested JSON payloads
across English, Hindi, Kannada, Marathi, Tamil, Telugu, and Gujarati.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.translation_service import translation_service
from app.core.logging import logger

router = APIRouter(prefix="/translate", tags=["Stage 16 — Multilingual Translation Engine"])


class TranslateTextRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (e.g. 'hi', 'kn', 'mr', 'ta', 'te', 'gu', 'en')")
    source_language: Optional[str] = Field(default="en", description="Source language code")


class TranslateTextResponse(BaseModel):
    success: bool = True
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


class TranslateBatchRequest(BaseModel):
    texts: List[str] = Field(..., description="List of strings to translate")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(default="en", description="Source language code")


class TranslateBatchResponse(BaseModel):
    success: bool = True
    translated_texts: List[str]
    target_language: str


class TranslateObjectRequest(BaseModel):
    data: Any = Field(..., description="Arbitrary JSON data object or list")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(default="en", description="Source language code")


class TranslateObjectResponse(BaseModel):
    success: bool = True
    data: Any
    target_language: str


@router.post("/text", response_model=TranslateTextResponse, status_code=status.HTTP_200_OK)
async def translate_single_text(request: TranslateTextRequest):
    """
    Translate a single string into target Indian language.
    """
    try:
        translated = await translation_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language or "en"
        )
        return TranslateTextResponse(
            success=True,
            original_text=request.text,
            translated_text=translated,
            source_language=request.source_language or "en",
            target_language=request.target_language
        )
    except Exception as e:
        logger.error(f"[TRANSLATION API ERROR] {e}", exc_info=True)
        return TranslateTextResponse(
            success=False,
            original_text=request.text,
            translated_text=request.text,
            source_language=request.source_language or "en",
            target_language=request.target_language
        )


@router.post("/batch", response_model=TranslateBatchResponse, status_code=status.HTTP_200_OK)
async def translate_batch_texts(request: TranslateBatchRequest):
    """
    Translate a list of strings into target Indian language.
    """
    try:
        translated_list = await translation_service.translate_batch(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language or "en"
        )
        return TranslateBatchResponse(
            success=True,
            translated_texts=translated_list,
            target_language=request.target_language
        )
    except Exception as e:
        logger.error(f"[TRANSLATION BATCH API ERROR] {e}", exc_info=True)
        return TranslateBatchResponse(
            success=False,
            translated_texts=request.texts,
            target_language=request.target_language
        )


@router.post("/object", response_model=TranslateObjectResponse, status_code=status.HTTP_200_OK)
async def translate_json_object(request: TranslateObjectRequest):
    """
    Translate all user-facing string fields in a JSON object/list recursively.
    Preserves IDs, numbers, booleans, and structure.
    """
    try:
        translated_data = await translation_service.translate_object(
            data=request.data,
            target_language=request.target_language,
            source_language=request.source_language or "en"
        )
        return TranslateObjectResponse(
            success=True,
            data=translated_data,
            target_language=request.target_language
        )
    except Exception as e:
        logger.error(f"[TRANSLATION OBJECT API ERROR] {e}", exc_info=True)
        return TranslateObjectResponse(
            success=False,
            data=request.data,
            target_language=request.target_language
        )
