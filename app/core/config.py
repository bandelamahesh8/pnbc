import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "Pragati Bharati - Document Intelligence & Question Extraction Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Scalable Document Processing & Question Extraction Service accepting PDFs and "
        "images containing examination material and converting them into structured, "
        "machine-readable questions with answer key association and confidence scoring."
    )
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="Secret key for JWT generation and verification"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./pnbc.db",
        description="Async database connection string. Can be PostgreSQL (postgresql+asyncpg://...) or SQLite (sqlite+aiosqlite://...)"
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./pnbc.db",
        description="Sync database connection string for Celery/Alembic. Can be PostgreSQL (postgresql+psycopg2://...) or SQLite (sqlite:///...)"
    )

    # Redis & Asynchronous Processing
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_ENABLED: bool = False
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for multimodal document intelligence"
    )
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Storage & Upload Rules
    STORAGE_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    # Confidence Thresholds
    CONFIDENCE_THRESHOLD_HIGH: float = 0.85
    CONFIDENCE_THRESHOLD_REVIEW: float = 0.70

    def get_celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    def get_celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL


settings = Settings()
