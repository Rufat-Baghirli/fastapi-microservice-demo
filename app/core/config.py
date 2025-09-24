# app/core/config.py
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "FastAPI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DESCRIPTION: str = "FastAPI Backend with async support"

    # API
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = Field(..., description="Async database connection URL")
    SYNC_DATABASE_URL: Optional[str] = Field(None, description="Sync database connection URL")
    RUN_MIGRATIONS_ON_STARTUP: bool = True

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=list)

    # Celery / Message Queue
    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    REDIS_URL: str = "redis://redis:6379/0"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return [origin.strip() for origin in json.loads(s)]
                except json.JSONDecodeError:
                    return [s.strip()]
            return [origin.strip() for origin in s.split(",") if origin.strip()]
        return v if isinstance(v, list) else []

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def set_sync_database_url(cls, v, values):
        if v:
            return v
        data = values.data if hasattr(values, 'data') else values
        if "DATABASE_URL" in data:
            return data["DATABASE_URL"].replace("+asyncpg", "")
        return v

    @field_validator("RUN_MIGRATIONS_ON_STARTUP", mode="before")
    @classmethod
    def convert_to_bool(cls, v) -> bool:
        if isinstance(v, str):
            return v.lower() in ('true', '1', 't', 'y', 'yes')
        return bool(v)


# Global settings instance
settings = Settings()