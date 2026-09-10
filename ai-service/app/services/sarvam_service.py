import httpx
from typing import Dict, Any, Tuple, Optional
from app.core.config import settings
from app.core.logging import logger

SARVAM_STT_ENDPOINT = "https://api.sarvam.ai/speech-to-text"

# Standard Sarvam Supported Language Code Mapping
SARVAM_LANGUAGE_MAP = {
    # English
    "en": "en-IN",
    "english": "en-IN",
    "en-in": "en-IN",
    "en_in": "en-IN",
    "en-us": "en-IN",
    "en-gb": "en-IN",
    # Hindi
    "hi": "hi-IN",
    "hindi": "hi-IN",
    "hi-in": "hi-IN",
    "hi_in": "hi-IN",
    # Kannada
    "kn": "kn-IN",
    "kannada": "kn-IN",
    "kn-in": "kn-IN",
    "kn_in": "kn-IN",
    # Marathi
    "mr": "mr-IN",
    "marathi": "mr-IN",
    "mr-in": "mr-IN",
    "mr_in": "mr-IN",
    # Tamil
    "ta": "ta-IN",
    "tamil": "ta-IN",
    "ta-in": "ta-IN",
    "ta_in": "ta-IN",
    # Telugu
    "te": "te-IN",
    "telugu": "te-IN",
    "te-in": "te-IN",
    "te_in": "te-IN",
    # Bengali
    "bn": "bn-IN",
    "bengali": "bn-IN",
    "bn-in": "bn-IN",
    "bn_in": "bn-IN",
    # Gujarati
    "gu": "gu-IN",
    "gujarati": "gu-IN",
    "gu-in": "gu-IN",
    "gu_in": "gu-IN",
    # Malayalam
    "ml": "ml-IN",
    "malayalam": "ml-IN",
    "ml-in": "ml-IN",
    "ml_in": "ml-IN",
    # Punjabi
    "pa": "pa-IN",
    "punjabi": "pa-IN",
    "pa-in": "pa-IN",
    "pa_in": "pa-IN",
    # Odia
    "od": "od-IN",
    "or": "od-IN",
    "odia": "od-IN",
    "od-in": "od-IN",
    "od_in": "od-IN",
    # Urdu
    "ur": "ur-IN",
    "urdu": "ur-IN",
    "ur-in": "ur-IN",
    "ur_in": "ur-IN",
    # Other Indic languages
    "as": "as-IN",
    "assamese": "as-IN",
    "ne": "ne-IN",
    "nepali": "ne-IN",
    "kok": "kok-IN",
    "konkani": "kok-IN",
    "ks": "ks-IN",
    "kashmiri": "ks-IN",
    "sd": "sd-IN",
    "sindhi": "sd-IN",
    "sa": "sa-IN",
    "sanskrit": "sa-IN",
    "sat": "sat-IN",
    "santali": "sat-IN",
    "mni": "mni-IN",
    "manipuri": "mni-IN",
    "brx": "brx-IN",
    "bodo": "brx-IN",
    "mai": "mai-IN",
    "maithili": "mai-IN",
    "doi": "doi-IN",
    "dogri": "doi-IN",
    # Auto / unknown
    "unknown": "unknown",
    "auto": "unknown",
}


def normalize_sarvam_language(language: Optional[str]) -> str:
    """
    Centralized language code normalization for Sarvam Saaras STT API.
    Guarantees returning ONLY valid Sarvam language codes.
    Defaults to 'unknown' if missing, unsupported, or ambiguous for automatic multi-dialect detection.
    """
    if not language or not str(language).strip():
        return "unknown"

    clean_lang = str(language).strip().lower()
    return SARVAM_LANGUAGE_MAP.get(clean_lang, "unknown")


def log_sarvam_config():
    """Development-safe configuration check at startup."""
    has_key = bool(settings.SARVAM_API_KEY and not settings.SARVAM_API_KEY.startswith("your_") and len(settings.SARVAM_API_KEY) > 8)
    model = settings.SARVAM_STT_MODEL or "saaras:v1"
    logger.info(f"[SARVAM CONFIG] API key configured: {has_key}")
    logger.info(f"[SARVAM CONFIG] STT model: {model}")
    logger.info("[SARVAM CONFIG] default language: unknown")


class SarvamSTTService:
    """
    Client for Sarvam AI Saaras Speech-to-Text API for Indian Multilingual Speech.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = settings.SARVAM_STT_MODEL or "saaras:v1"

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: str = "audio/webm",
        language_code: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Sends audio to Sarvam Saaras STT and returns (transcript, detected_language_code).
        Uses centralized language normalization and safe MIME type handling.
        """
        if not self.api_key or self.api_key.startswith("your_") or len(self.api_key) < 8:
            logger.warning("[SARVAM STT] API key is not configured or placeholder.")
            raise ValueError(
                "Sarvam API key is not configured. Please add a valid SARVAM_API_KEY in .env or switch to text intake."
            )

        # 1. Centralized language code normalization
        normalized_lang = normalize_sarvam_language(language_code)

        # 2. Normalize content-type (e.g. 'audio/webm;codecs=opus' -> 'audio/webm')
        clean_content_type = content_type.split(";")[0].strip() if content_type else "audio/webm"
        if not filename or filename == "blob":
            filename = "recording.webm" if "webm" in clean_content_type else "recording.wav"

        # 3. Structured Debug Logging (no secret exposure)
        logger.info(f"[VOICE DEBUG] frontend_language='{language_code}'")
        logger.info(f"[VOICE DEBUG] received_language='{language_code}'")
        logger.info(f"[VOICE DEBUG] normalized_language='{normalized_lang}'")
        logger.info(f"[VOICE DEBUG] sarvam_language_code='{normalized_lang}'")
        logger.info(f"[SARVAM STT] audio_mime_type='{clean_content_type}'")
        logger.info(f"[SARVAM STT] audio_size={len(audio_bytes)} bytes")

        headers = {
            "api-subscription-key": self.api_key,
        }

        files = {
            "file": (filename, audio_bytes, clean_content_type)
        }
        data = {
            "model": self.model,
            "language_code": normalized_lang
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    SARVAM_STT_ENDPOINT,
                    headers=headers,
                    files=files,
                    data=data
                )

                if response.status_code != 200:
                    logger.error(f"[SARVAM STT ERROR] Status {response.status_code}: {response.text}")
                    try:
                        err_json = response.json()
                        err_msg = err_json.get("message") or err_json.get("error", {}).get("message") or response.text
                    except Exception:
                        err_msg = response.text
                    raise RuntimeError(f"Sarvam STT rejected request ({response.status_code}): {err_msg}")

                result = response.json()
                transcript = result.get("transcript", "").strip()
                detected_lang = result.get("language_code", normalized_lang)
                
                simple_code = detected_lang.split("-")[0].lower() if (detected_lang and detected_lang != "unknown") else (language_code or "en")

                logger.info(f"[SARVAM STT SUCCESS] detected_lang='{detected_lang}', simple_code='{simple_code}', transcript_length={len(transcript)}")
                return transcript, simple_code

        except httpx.RequestError as e:
            logger.error(f"[SARVAM STT NETWORK ERROR] {e}")
            raise RuntimeError(f"Network error communicating with Sarvam STT: {e}")
        except Exception as e:
            logger.error(f"[SARVAM STT UNEXPECTED ERROR] {e}")
            raise


sarvam_stt_service = SarvamSTTService()
