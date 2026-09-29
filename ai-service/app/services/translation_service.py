"""
Stage 16: KALPA Enterprise Multilingual Translation Service.
Provides high-accuracy, ultra-low-latency translation between English and Indian languages
(Hindi, Kannada, Marathi, Tamil, Telugu, Gujarati, Bengali, Malayalam, Punjabi, Odia) using:
1. Google Cloud Translation API (if GOOGLE_TRANSLATION_API_KEY is configured)
2. High-speed Direct Google Translate Engine (clients5 dict-chrome-ex)
3. Sarvam AI Mayura Translation API & MyMemory Translation fallback
4. Sarvam / Groq LLM-powered context-aware translation fallback
5. In-memory fast cache to ensure sub-millisecond retrieval on repeated text
"""
import os
import asyncio
import logging
import json
import html
import urllib.parse
from typing import Dict, Any, List, Optional, Union
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_CLOUD_TRANSLATE_ENDPOINT = "https://translation.googleapis.com/language/translate/v2"
GOOGLE_CLIENT_TRANSLATE_ENDPOINT = "https://clients5.google.com/translate_a/t"
SARVAM_TRANSLATE_ENDPOINT = "https://api.sarvam.ai/translate"
MYMEMORY_TRANSLATE_ENDPOINT = "https://api.mymemory.translated.net/get"

# ISO 639-1 Language Code Mapping for Google Translation
LANGUAGE_CODE_TO_GOOGLE = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
    "mr": "mr",
    "ta": "ta",
    "te": "te",
    "gu": "gu",
    "bn": "bn",
    "ml": "ml",
    "pa": "pa",
    "or": "or",
    "od": "or",
}

# Language Mapping for Sarvam Translation
LANGUAGE_CODE_TO_SARVAM = {
    "en": "en-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "od": "od-IN",
    "or": "od-IN",
}

# In-memory fast cache: key=(source_lang, target_lang, text_hash) -> translated_text
_TRANSLATION_CACHE: Dict[str, str] = {}
_MAX_CACHE_SIZE = 50000

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
}


def _get_cache_key(src_lang: str, tgt_lang: str, text: str) -> str:
    return f"{src_lang}:{tgt_lang}:{text.strip()}"


class TranslationService:
    """
    Enterprise-grade multilingual translation engine for KALPA.
    Translates static and dynamic content across 7+ Indian languages with sub-second latency.
    """

    def __init__(self):
        self.google_api_key = (
            os.environ.get("GOOGLE_TRANSLATION_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or getattr(settings, "GOOGLE_TRANSLATION_API_KEY", None)
            or getattr(settings, "GOOGLE_API_KEY", None)
        )
        self.sarvam_api_key = settings.SARVAM_API_KEY
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                headers=HTTP_HEADERS,
                timeout=httpx.Timeout(12.0, connect=5.0),
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
            )
        return self._http_client

    def _normalize_google_lang(self, lang: Optional[str]) -> str:
        if not lang:
            return "en"
        clean = lang.strip().lower().split("-")[0]
        return LANGUAGE_CODE_TO_GOOGLE.get(clean, clean)

    def _normalize_sarvam_lang(self, lang: Optional[str]) -> str:
        if not lang:
            return "en-IN"
        clean = lang.strip().lower()
        if clean in LANGUAGE_CODE_TO_SARVAM:
            return LANGUAGE_CODE_TO_SARVAM[clean]
        if "-in" in clean:
            return clean
        return "en-IN"

    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        mode: str = "formal"
    ) -> str:
        """
        Translates a single string from source_language to target_language.
        Returns the original text if source and target match or if text is empty/numeric.
        """
        if not text or not isinstance(text, str) or not text.strip():
            return text or ""

        clean_text = text.strip()

        # If text is purely numeric, currency code, or special chars, no translation needed
        stripped = (
            clean_text.replace(".", "")
            .replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("%", "")
            .replace("x", "")
            .replace("X", "")
            .replace("-", "")
            .replace("/", "")
            .replace(":", "")
            .replace(" ", "")
        )
        if stripped.isdigit():
            return text

        src_google = self._normalize_google_lang(source_language)
        tgt_google = self._normalize_google_lang(target_language)

        if src_google == tgt_google:
            return text

        # Check in-memory cache
        cache_key = _get_cache_key(src_google, tgt_google, clean_text)
        if cache_key in _TRANSLATION_CACHE:
            return _TRANSLATION_CACHE[cache_key]

        client = self._get_client()

        # 1. Primary: Google Cloud Translation API v2 (if valid API key is present)
        if self.google_api_key and not self.google_api_key.startswith("your_") and len(self.google_api_key.strip()) > 8:
            try:
                params = {
                    "key": self.google_api_key.strip(),
                    "q": clean_text,
                    "target": tgt_google,
                    "source": src_google,
                    "format": "text"
                }
                resp = await client.post(GOOGLE_CLOUD_TRANSLATE_ENDPOINT, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    translations = data.get("data", {}).get("translations", [])
                    if translations and "translatedText" in translations[0]:
                        result = html.unescape(translations[0]["translatedText"]).strip()
                        if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                            _TRANSLATION_CACHE[cache_key] = result
                        return result
            except Exception as e:
                logger.warning(f"[TRANSLATE GOOGLE CLOUD] Error: {e}")

        # 2. Google Translate High-Speed Direct Engine (clients5 dict-chrome-ex)
        try:
            params = {
                "client": "dict-chrome-ex",
                "sl": src_google,
                "tl": tgt_google,
                "q": clean_text,
            }
            resp = await client.get(GOOGLE_CLIENT_TRANSLATE_ENDPOINT, params=params)
            if resp.status_code == 200:
                data = resp.json()
                raw = data[0] if isinstance(data, list) else str(data)
                result = html.unescape(raw).strip()
                if result:
                    if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                        _TRANSLATION_CACHE[cache_key] = result
                    return result
        except Exception as e:
            logger.warning(f"[TRANSLATE GOOGLE ENGINE] Error: {e}")

        # 3. Fallback: MyMemory Translation API
        try:
            params = {
                "q": clean_text,
                "langpair": f"{src_google}|{tgt_google}"
            }
            resp = await client.get(MYMEMORY_TRANSLATE_ENDPOINT, params=params)
            if resp.status_code == 200:
                data = resp.json()
                trans = data.get("responseData", {}).get("translatedText")
                if trans and isinstance(trans, str) and trans.strip():
                    result = html.unescape(trans).strip()
                    if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                        _TRANSLATION_CACHE[cache_key] = result
                    return result
        except Exception as e:
            logger.warning(f"[TRANSLATE MYMEMORY] Error: {e}")

        # 4. Fallback: Sarvam Mayura Translation API
        if self.sarvam_api_key and not self.sarvam_api_key.startswith("your_") and len(self.sarvam_api_key.strip()) > 8:
            try:
                src_sarvam = self._normalize_sarvam_lang(source_language)
                tgt_sarvam = self._normalize_sarvam_lang(target_language)
                headers = {
                    "api-subscription-key": self.sarvam_api_key.strip(),
                    "Content-Type": "application/json"
                }
                payload = {
                    "input": clean_text,
                    "source_language_code": src_sarvam,
                    "target_language_code": tgt_sarvam,
                    "speaker_gender": "Female",
                    "mode": mode,
                    "model": "mayura:v1",
                    "enable_preprocessing": True
                }
                resp = await client.post(SARVAM_TRANSLATE_ENDPOINT, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    translated = data.get("translated_text") or data.get("output")
                    if translated and isinstance(translated, str) and translated.strip():
                        result = html.unescape(translated).strip()
                        if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                            _TRANSLATION_CACHE[cache_key] = result
                        return result
            except Exception as e:
                logger.warning(f"[TRANSLATE SARVAM API] Error: {e}")

        # 5. Fallback: LLM Translation (Groq / Sarvam)
        try:
            translated_llm = await self._translate_with_llm(clean_text, src_google, tgt_google)
            if translated_llm:
                if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                    _TRANSLATION_CACHE[cache_key] = translated_llm
                return translated_llm
        except Exception as e:
            logger.warning(f"[TRANSLATE LLM] Fallback error: {e}")

        # Return original text if all translation methods fail
        return text

    async def _translate_with_llm(self, text: str, src_lang: str, tgt_lang: str) -> Optional[str]:
        """
        Translates text using Groq or Sarvam LLM with a strict prompt.
        """
        target_name_map = {
            "hi": "Hindi",
            "kn": "Kannada",
            "mr": "Marathi",
            "ta": "Tamil",
            "te": "Telugu",
            "gu": "Gujarati",
            "bn": "Bengali",
            "ml": "Malayalam",
            "pa": "Punjabi",
            "or": "Odia",
            "en": "English"
        }
        target_name = target_name_map.get(tgt_lang, "Hindi")
        client = self._get_client()

        # Try Groq LLM
        if settings.active_llm_api_key and settings.active_llm_provider == "groq":
            try:
                headers = {
                    "Authorization": f"Bearer {settings.active_llm_api_key}",
                    "Content-Type": "application/json"
                }
                messages = [
                    {
                        "role": "system",
                        "content": f"Translate the following text accurately into {target_name}. Preserve currency symbols, numbers, and proper business nouns. Return ONLY the translated string without quotes or preamble."
                    },
                    {"role": "user", "content": text}
                ]
                payload = {
                    "model": settings.GROQ_MODEL or "qwen/qwen3.6-27b",
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 400
                }
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices") or []
                    if choices and "message" in choices[0]:
                        res = choices[0]["message"].get("content", "").strip()
                        if res:
                            return html.unescape(res.strip('"').strip("'"))
            except Exception as e:
                logger.warning(f"[TRANSLATE GROQ LLM] Error: {e}")

        return None

    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: str = "en"
    ) -> List[str]:
        """
        Translates a list of strings with batching, concurrency, and caching.
        """
        if not texts:
            return []

        src_google = self._normalize_google_lang(source_language)
        tgt_google = self._normalize_google_lang(target_language)

        if src_google == tgt_google:
            return texts

        uncached_indices = []
        uncached_texts = []
        results = [None] * len(texts)

        for idx, t in enumerate(texts):
            if not t or not isinstance(t, str) or not t.strip():
                results[idx] = t or ""
                continue
            clean = t.strip()
            cache_key = _get_cache_key(src_google, tgt_google, clean)
            if cache_key in _TRANSLATION_CACHE:
                results[idx] = _TRANSLATION_CACHE[cache_key]
            else:
                uncached_indices.append(idx)
                uncached_texts.append(clean)

        if not uncached_texts:
            return results

        # 1. Google Cloud Translation API v2 Batch (if API key present)
        if self.google_api_key and not self.google_api_key.startswith("your_") and len(self.google_api_key.strip()) > 8:
            try:
                params = {
                    "key": self.google_api_key.strip(),
                    "target": tgt_google,
                    "source": src_google,
                    "format": "text"
                }
                client = self._get_client()
                resp = await client.post(GOOGLE_CLOUD_TRANSLATE_ENDPOINT, params=params, json={"q": uncached_texts})
                if resp.status_code == 200:
                    data = resp.json()
                    trans_list = data.get("data", {}).get("translations", [])
                    for i, tr in enumerate(trans_list):
                        trans_text = html.unescape(tr.get("translatedText", uncached_texts[i])).strip()
                        orig_idx = uncached_indices[i]
                        results[orig_idx] = trans_text
                        c_key = _get_cache_key(src_google, tgt_google, uncached_texts[i])
                        if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                            _TRANSLATION_CACHE[c_key] = trans_text

                    for idx in range(len(results)):
                        if results[idx] is None:
                            results[idx] = texts[idx]
                    return results
            except Exception as e:
                logger.warning(f"[BATCH GOOGLE CLOUD ERROR] {e}")

        # 2. Fast Delimiter Batching with Direct Google Translate Engine
        # Only attempt if total string size is reasonable (< 3500 chars)
        total_len = sum(len(x) for x in uncached_texts)
        if len(uncached_texts) <= 40 and total_len < 3500:
            try:
                delimiter = " ||| "
                combined = delimiter.join(uncached_texts)
                client = self._get_client()
                params = {
                    "client": "dict-chrome-ex",
                    "sl": src_google,
                    "tl": tgt_google,
                    "q": combined
                }
                resp = await client.get(GOOGLE_CLIENT_TRANSLATE_ENDPOINT, params=params)
                if resp.status_code == 200:
                    d = resp.json()
                    raw = d[0] if isinstance(d, list) else str(d)
                    raw_unescaped = html.unescape(raw)
                    parts = [p.strip() for p in raw_unescaped.split("|||")]
                    if len(parts) == len(uncached_texts):
                        for i, p in enumerate(parts):
                            orig_idx = uncached_indices[i]
                            results[orig_idx] = p
                            c_key = _get_cache_key(src_google, tgt_google, uncached_texts[i])
                            if len(_TRANSLATION_CACHE) < _MAX_CACHE_SIZE:
                                _TRANSLATION_CACHE[c_key] = p
                        for idx in range(len(results)):
                            if results[idx] is None:
                                results[idx] = texts[idx]
                        return results
            except Exception as e:
                logger.warning(f"[BATCH DELIMITER ERROR] {e}")

        # 3. Concurrent translation with semaphore
        sem = asyncio.Semaphore(30)

        async def _fetch_single(orig_idx: int, txt: str):
            async with sem:
                trans = await self.translate_text(txt, tgt_google, src_google)
                results[orig_idx] = trans

        tasks = [
            _fetch_single(uncached_indices[i], uncached_texts[i])
            for i in range(len(uncached_texts))
            if results[uncached_indices[i]] is None
        ]
        if tasks:
            await asyncio.gather(*tasks)

        # Fill any remaining with originals
        for idx in range(len(results)):
            if results[idx] is None:
                results[idx] = texts[idx]

        return results

    async def translate_object(
        self,
        data: Any,
        target_language: str,
        source_language: str = "en",
        keys_to_skip: Optional[List[str]] = None
    ) -> Any:
        """
        Recursively translates all string values in a dictionary or list,
        preserving original keys, numeric values, booleans, and nested structure.
        """
        if target_language in ["en", "en-IN"] and source_language in ["en", "en-IN"]:
            return data

        skip_keys = set(keys_to_skip or [
            "id", "uuid", "analysis_id", "session_id", "business_id", "created_at",
            "updated_at", "status", "intent", "provider", "model", "type", "key",
            "code", "unit", "color", "icon", "url", "email", "phone", "pincode",
            "dscr_ratio", "loan_amount", "monthly_emi", "payback_period_months"
        ])

        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k in skip_keys:
                    new_dict[k] = v
                elif isinstance(v, str):
                    new_dict[k] = await self.translate_text(v, target_language, source_language)
                elif isinstance(v, (dict, list)):
                    new_dict[k] = await self.translate_object(v, target_language, source_language, keys_to_skip)
                else:
                    new_dict[k] = v
            return new_dict
        elif isinstance(data, list):
            return [
                await self.translate_object(item, target_language, source_language, keys_to_skip)
                if isinstance(item, (dict, list, str)) else item
                for item in data
            ]
        elif isinstance(data, str):
            return await self.translate_text(data, target_language, source_language)
        return data


translation_service = TranslationService()
