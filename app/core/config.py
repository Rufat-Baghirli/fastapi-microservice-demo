from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os
import sys
from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),   # default .env
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

    @classmethod
    def _parse_cors(cls, v) -> List[str]:
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    return [o.strip() for o in parsed if isinstance(o, str)]
                except json.JSONDecodeError:
                    return [s]
            return [origin.strip() for origin in s.split(",") if origin.strip()]
        return v if isinstance(v, list) else []

    from pydantic import field_validator

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        return cls._parse_cors(v)

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def set_sync_database_url(cls, v, info):
        if v:
            return v
        values = info.data if hasattr(info, "data") else info
        db_url = values.get("DATABASE_URL") or os.getenv("DATABASE_URL") or ""
        if db_url:
            return db_url.replace("+asyncpg", "")
        return v

    @field_validator("RUN_MIGRATIONS_ON_STARTUP", mode="before")
    @classmethod
    def convert_to_bool(cls, v) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "y", "yes")
        return bool(v)

    @property
    def SYNC_DB(self) -> Optional[str]:
        return self.SYNC_DATABASE_URL or (self.DATABASE_URL.replace("+asyncpg", "") if self.DATABASE_URL else None)


def get_settings(env_file: Optional[str] = None) -> Settings:
    try:
        if env_file:
            return Settings(_env_file=str(env_file))
        return Settings()
    except ValidationError as exc:
        print("⚠️ Settings validation error. Check environment variables and .env files.", file=sys.stderr)
        print(exc, file=sys.stderr)
        raise


settings = get_settings()
