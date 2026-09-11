import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger


def log_llm_config():
    """
    Startup diagnostics logging LLM provider, configuration status, and model.
    Guarantees secrets are never exposed in logs.
    """
    provider = settings.active_llm_provider
    is_configured = settings.is_llm_configured
    model = settings.active_llm_model

    logger.info(f"[LLM CONFIG] provider='{provider}'")
    logger.info(f"[LLM CONFIG] api_key_configured={is_configured}")
    logger.info(f"[LLM CONFIG] model='{model}'")


class LLMClient:
    """
    Centralized, resilient LLM client supporting Groq and standard OpenAI-compatible endpoints.
    Provides safe lazy initialization, rate-limit protection, and fallback safety.
    """

    def __init__(self):
        self._initialized = False
        self._provider: Optional[str] = None
        self._model: Optional[str] = None
        self._endpoint: Optional[str] = None

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True

        if not settings.is_llm_configured:
            return False

        self._provider = settings.active_llm_provider
        self._model = settings.active_llm_model

        if self._provider == "groq" or (settings.active_llm_api_key and settings.active_llm_api_key.startswith("gsk_")):
            self._endpoint = "https://api.groq.com/openai/v1/chat/completions"
        else:
            self._endpoint = "https://api.openai.com/v1/chat/completions"

        self._initialized = True
        logger.info(f"[LLM CLIENT INITIALIZED] provider='{self._provider}', model='{self._model}'")
        return True

    @property
    def is_available(self) -> bool:
        return settings.is_llm_configured

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        max_tokens: int = 300,
        temperature: float = 0.0,
        timeout: float = 15.0
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a chat completion request with defensive error handling and timeout protection.
        Returns parsed JSON dict (if json_mode=True) or dict with 'text' content, or None on failure.
        """
        if not settings.is_llm_configured:
            logger.info("[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: API key not configured")
            return None

        self._ensure_initialized()
        api_key = settings.active_llm_api_key

        payload: Dict[str, Any] = {
            "model": self._model or settings.active_llm_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self._endpoint or "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    if json_mode:
                        parsed = json.loads(content)
                        return parsed
                    return {"text": content}
                else:
                    logger.warning(
                        f"[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: "
                        f"API status {response.status_code} ({response.text[:200]})"
                    )
                    return None

        except httpx.TimeoutException:
            logger.warning("[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: Request timeout")
            return None
        except httpx.RequestError as e:
            logger.warning(f"[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: Network error ({e})")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: JSON decode failure ({e})")
            return None
        except Exception as e:
            logger.warning(f"[LLM CLASSIFIER FALLBACK] Groq unavailable, using deterministic fallback: Unexpected error ({e})")
            return None


llm_client = LLMClient()
