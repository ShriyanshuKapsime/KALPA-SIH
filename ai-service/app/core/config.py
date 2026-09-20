import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server Configuration
    PROJECT_NAME: str = "KALPA AI Service"
    TAGLINE: str = "AI-Powered Hyper-Local Livelihood & Business Advisory Platform for Rural Bharat"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database & Spatial Config
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "kalpa"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DATABASE_URL: Optional[str] = None
    POSTGIS_ENABLED: bool = True
    PGVECTOR_ENABLED: bool = False

    # Phase 1 & 2 AI / LLM Provider (Groq / Qwen / OpenAI)
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: Optional[str] = None

    @property
    def active_llm_provider(self) -> str:
        return (self.LLM_PROVIDER or "groq").lower().strip()

    @property
    def active_llm_api_key(self) -> Optional[str]:
        key = self.GROQ_API_KEY or self.LLM_API_KEY
        if key and not key.startswith("your_") and len(key.strip()) > 5:
            return key.strip()
        return None

    @property
    def active_llm_model(self) -> str:
        if self.active_llm_provider == "groq":
            raw_model = self.GROQ_MODEL or self.LLM_MODEL or "llama-3.3-70b-versatile"
            # Normalize invalid model identifiers or prefixes for Groq
            clean_m = raw_model.strip()
            if "qwen3.6" in clean_m.lower() or clean_m.lower().startswith("qwen/"):
                return "llama-3.3-70b-versatile"
            return clean_m
        return self.LLM_MODEL or self.GROQ_MODEL or "gpt-4o"

    @property
    def is_llm_configured(self) -> bool:
        return bool(self.active_llm_api_key)

    # Sarvam AI STT, TTS & LLM
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_STT_MODEL: str = "saaras:v4"
    SARVAM_TTS_MODEL: str = "bulbul:v3"
    SARVAM_TTS_SPEAKER: str = "shreya"
    SARVAM_LLM_MODEL: str = "sarvam-105b"
    SARVAM_ASSISTANT_MODEL: str = "sarvam-105b-conversations"
    SARVAM_ASSISTANT_TIMEOUT: float = 90.0
    SARVAM_LLM_ENABLED: bool = True
    SARVAM_LLM_ENDPOINT: str = "https://api.sarvam.ai/v1/chat/completions"

    @property
    def is_sarvam_configured(self) -> bool:
        return bool(self.SARVAM_API_KEY and not self.SARVAM_API_KEY.startswith("your_") and len(self.SARVAM_API_KEY.strip()) > 8)

    @property
    def is_sarvam_llm_enabled(self) -> bool:
        return self.is_sarvam_configured and self.SARVAM_LLM_ENABLED

    # Multilingual Translation
    INDICTRANS_ENABLED: bool = False

    # RAG & Embedding Config
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
