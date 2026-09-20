import io
import wave
import base64
import re
import httpx
from typing import Dict, Any, Tuple, Optional, List
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


def clean_text_for_speech(text: str, language: str = "en") -> str:
    """
    Prepares text for natural text-to-speech synthesis by stripping Markdown syntax,
    code blocks, UI annotations, stage tags, and formatting numbered lists smoothly.
    """
    if not text or not text.strip():
        return ""

    t = text.strip()

    # Remove code blocks
    t = re.sub(r"```[\s\S]*?```", "", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # Remove stage tags / metadata brackets like [STAGE 9], [VERIFIED], etc.
    t = re.sub(r"\[(?:STAGE\s*\d+|VERIFIED|GROUNDED|SOURCE|CANONICAL)[^\]]*\]", "", t, flags=re.IGNORECASE)

    # Convert markdown links [text](url) -> text
    t = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", t)

    # Convert headings (e.g. ### Heading -> Heading.)
    t = re.sub(r"#{1,6}\s*(.+)", r"\1.\n", t)

    # Convert bold / italic markers
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"_([^_]+)_", r"\1", t)

    # Clean bullet points (- item or * item or • item -> item.)
    t = re.sub(r"^\s*[-*•]\s*(.+)$", r"\1.", t, flags=re.MULTILINE)

    # Clean numbered lists
    lines = []
    for line in t.split("\n"):
        num_match = re.match(r"^\s*(\d+)\.\s*(.+)$", line)
        if num_match:
            item_content = num_match.group(2).strip()
            lines.append(f"{item_content}.")
        else:
            lines.append(line)
    t = "\n".join(lines)

    # Strip table dividers |---|---|
    t = re.sub(r"\|[\s\-:]+\|", "", t)
    # Replace table pipe separators with commas or spaces
    t = re.sub(r"\|\s*", ", ", t)

    # Clean up double periods, trailing punctuation, and excessive whitespace
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r"\s+", " ", t).strip()

    return t


def split_text_for_tts(text: str, max_chars: int = 500) -> List[str]:
    """
    Intelligently chunks text for Sarvam Bulbul v3 TTS API (max 500 chars per chunk).
    Preserves Hindi (Devanagari) & English sentences, respects natural sentence boundaries
    (।, ॥, ., ?, !, \n, whitespace) and never breaks words unless unavoidable.
    """
    if not text or not str(text).strip():
        return []

    clean = str(text).strip()
    if len(clean) <= max_chars:
        return [clean]

    # Split into paragraphs first
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [clean]

    sentence_pattern = re.compile(r'([^।॥.?!;\n]+[।॥.?!;\n]*)')

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # Check if adding the whole paragraph to current_chunk fits
        candidate = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
        if len(candidate) <= max_chars:
            current_chunk = candidate
            continue

        # If current_chunk already has content and para alone fits, flush current_chunk
        if len(para) <= max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
            continue

        # If para itself > max_chars, break down into sentences
        raw_sentences = sentence_pattern.findall(para)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            sentences = [para]

        for sentence in sentences:
            cand_sent = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
            if len(cand_sent) <= max_chars:
                current_chunk = cand_sent
                continue

            # If current_chunk has content, flush it
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # If the single sentence fits in max_chars
            if len(sentence) <= max_chars:
                current_chunk = sentence
                continue

            # If single sentence exceeds max_chars, split on words (whitespace)
            words = sentence.split(" ")
            for word in words:
                if not word:
                    continue
                cand_word = f"{current_chunk} {word}".strip() if current_chunk else word
                if len(cand_word) <= max_chars:
                    current_chunk = cand_word
                    continue

                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # If single word > max_chars (e.g. extremely long string without spaces)
                if len(word) > max_chars:
                    for k in range(0, len(word), max_chars):
                        sub = word[k:k+max_chars]
                        if len(sub) == max_chars:
                            chunks.append(sub)
                        else:
                            current_chunk = sub
                else:
                    current_chunk = word

    if current_chunk and current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Final sanity check: guarantee no chunk > max_chars and no empty chunks
    verified = []
    for c in chunks:
        c_str = c.strip()
        if not c_str:
            continue
        if len(c_str) <= max_chars:
            verified.append(c_str)
        else:
            for k in range(0, len(c_str), max_chars):
                sub = c_str[k:k+max_chars].strip()
                if sub:
                    verified.append(sub)

    return verified



def concatenate_wav_audios(base64_wav_list: List[str]) -> str:
    """
    Concatenates multiple base64-encoded WAV audio files into a single valid base64 WAV file.
    Uses Python's standard wave library to combine raw PCM frames and generate a single valid RIFF header.
    """
    valid_audios = [b for b in base64_wav_list if b and isinstance(b, str) and len(b) > 10]
    if not valid_audios:
        return ""
    if len(valid_audios) == 1:
        return valid_audios[0]

    output_io = io.BytesIO()
    output_wav = None

    try:
        for b64_str in valid_audios:
            raw_bytes = base64.b64decode(b64_str)
            input_io = io.BytesIO(raw_bytes)
            with wave.open(input_io, 'rb') as w_in:
                if output_wav is None:
                    output_wav = wave.open(output_io, 'wb')
                    output_wav.setparams(w_in.getparams())
                frames = w_in.readframes(w_in.getnframes())
                output_wav.writeframes(frames)

        if output_wav:
            output_wav.close()

        return base64.b64encode(output_io.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"[ASSISTANT TTS CONCAT ERROR] Failed to concatenate WAV chunks: {e}", exc_info=True)
        return valid_audios[0]


class SarvamSTTService:
    """
    Client for Sarvam AI Saaras Speech-to-Text API for Indian Multilingual Speech.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = settings.SARVAM_STT_MODEL or "saaras:v4"

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
        logger.info(f"[VOICE DEBUG] normalized_language='{normalized_lang}'")
        logger.info(f"[SARVAM STT] audio_mime_type='{clean_content_type}', size={len(audio_bytes)} bytes, model='{self.model}'")

        headers = {
            "api-subscription-key": self.api_key.strip(),
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


SARVAM_TTS_ENDPOINT = "https://api.sarvam.ai/text-to-speech"

VALID_BULBUL_V3_SPEAKERS = {
    "aditya", "ritu", "ashutosh", "priya", "neha", "rahul", "pooja", "rohan",
    "simran", "kavya", "amit", "dev", "ishita", "shreya", "ratan", "varun",
    "manan", "sumit", "roopa", "kabir", "aayan", "shubh", "advait", "anand",
    "tanya", "tarun", "sunny", "mani", "gokul", "vijay", "shruti", "suhani",
    "mohit", "kavitha", "rehan", "soham", "rupali",
}
DEFAULT_TTS_SPEAKER = "shreya"


def validate_and_resolve_speaker(speaker: Optional[str]) -> str:
    """
    Validates that the requested speaker is in the recognized Bulbul v3 speaker catalog.
    If invalid or missing (e.g. legacy 'meera'), safely falls back to 'shreya' with diagnostic logging.
    """
    if not speaker or not str(speaker).strip():
        configured_default = getattr(settings, "SARVAM_TTS_SPEAKER", DEFAULT_TTS_SPEAKER)
        if configured_default and str(configured_default).strip().lower() in VALID_BULBUL_V3_SPEAKERS:
            return str(configured_default).strip().lower()
        return DEFAULT_TTS_SPEAKER

    clean_speaker = str(speaker).strip().lower()
    if clean_speaker in VALID_BULBUL_V3_SPEAKERS:
        return clean_speaker

    logger.warning(
        f"[ASSISTANT TTS] Invalid configured speaker='{speaker}'; falling back to '{DEFAULT_TTS_SPEAKER}'."
    )
    return DEFAULT_TTS_SPEAKER


class SarvamTTSService:
    """
    Client for Sarvam AI Bulbul Text-to-Speech API for Indian Multilingual Speech Synthesis.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = getattr(settings, "SARVAM_TTS_MODEL", "bulbul:v3") or "bulbul:v3"

    async def synthesize_speech(
        self,
        text: str,
        language_code: Optional[str] = "hi",
        speaker: Optional[str] = None,
        pace: float = 1.0,
        pitch: float = 0.0,
        loudness: float = 1.5,
        sample_rate: int = 22050
    ) -> Dict[str, Any]:
        """
        Synthesizes text into audio using Sarvam Bulbul TTS with intelligent chunking (<= 500 chars).
        Concatenates all resulting WAV chunks seamlessly into a single playable audio payload.
        """
        if not self.api_key or self.api_key.startswith("your_") or len(self.api_key) < 8:
            logger.warning("[SARVAM TTS] API key is not configured or placeholder.")
            raise ValueError(
                "Sarvam API key is not configured. Please add a valid SARVAM_API_KEY in .env."
            )

        clean_text = clean_text_for_speech(text, language=language_code or "en")
        if not clean_text:
            raise ValueError("No speakable text content found after cleaning.")

        normalized_lang = normalize_sarvam_language(language_code)
        if normalized_lang == "unknown":
            normalized_lang = "hi-IN" if (language_code and "hi" in language_code.lower()) else "en-IN"

        resolved_speaker = validate_and_resolve_speaker(speaker or getattr(settings, "SARVAM_TTS_SPEAKER", DEFAULT_TTS_SPEAKER))

        # Intelligent chunking for Sarvam Bulbul v3 500 char limit
        chunks = split_text_for_tts(clean_text, max_chars=500)
        if not chunks:
            raise ValueError("No speakable text chunks generated.")

        logger.info(
            f"[ASSISTANT TTS] model={self.model} language={normalized_lang} speaker={resolved_speaker} original_text_length={len(clean_text)} chunk_count={len(chunks)}"
        )

        headers = {
            "api-subscription-key": self.api_key.strip(),
            "Content-Type": "application/json"
        }

        audio_chunks: List[str] = []

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                for idx, chunk in enumerate(chunks):
                    logger.info(
                        f"[ASSISTANT TTS CHUNK] index={idx + 1} total={len(chunks)} length={len(chunk)}"
                    )

                    payload = {
                        "inputs": [chunk],
                        "target_language_code": normalized_lang,
                        "speaker": resolved_speaker,
                        "pitch": pitch,
                        "pace": pace,
                        "loudness": loudness,
                        "speech_sample_rate": sample_rate,
                        "enable_preprocessing": True,
                        "model": self.model
                    }

                    response = await client.post(
                        SARVAM_TTS_ENDPOINT,
                        headers=headers,
                        json=payload
                    )

                    if response.status_code != 200:
                        logger.error(f"[SARVAM TTS ERROR] Status {response.status_code}: {response.text}")
                        try:
                            err_json = response.json()
                            err_msg = err_json.get("message") or err_json.get("error", {}).get("message") or response.text
                        except Exception:
                            err_msg = response.text
                        raise RuntimeError(f"Sarvam TTS request failed for chunk {idx + 1}/{len(chunks)} ({response.status_code}): {err_msg}")

                    data = response.json()
                    audios = data.get("audios", [])
                    if not audios or not audios[0]:
                        raise RuntimeError(f"Sarvam TTS returned empty audio list for chunk {idx + 1}/{len(chunks)}.")

                    audio_chunks.append(audios[0])

            # Concatenate all generated WAV audio chunks into a single seamless audio file
            final_audio_base64 = concatenate_wav_audios(audio_chunks)

            logger.info(
                f"[ASSISTANT TTS SUCCESS] chunks={len(chunks)} total_chars={len(clean_text)} speaker={resolved_speaker} language={normalized_lang}"
            )
            return {
                "success": True,
                "audio_base64": final_audio_base64,
                "format": "audio/wav",
                "mime_type": "audio/wav",
                "language_code": normalized_lang,
                "speaker": resolved_speaker,
                "spoken_text": clean_text,
                "chunk_count": len(chunks)
            }

        except httpx.RequestError as e:
            logger.error(f"[SARVAM TTS NETWORK ERROR] {e}")
            raise RuntimeError(f"Network error communicating with Sarvam TTS: {e}")


sarvam_stt_service = SarvamSTTService()
sarvam_tts_service = SarvamTTSService()


