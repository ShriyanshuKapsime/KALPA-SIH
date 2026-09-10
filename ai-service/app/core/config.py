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

    # Phase 1 AI / LLM Provider (Groq / Qwen / OpenAI)
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "qwen/qwen3.6-27b"
    LLM_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Sarvam AI STT
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_STT_MODEL: str = "saaras:v4"

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
