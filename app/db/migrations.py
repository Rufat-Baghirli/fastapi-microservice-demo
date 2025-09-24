# app/db/migrations.py
import os
from alembic.config import Config
from alembic import command
from typing import Optional
from pathlib import Path
from app.core.config import settings

def get_alembic_config(alembic_ini_path: Optional[str] = None) -> Config:
    """
    Load alembic Config and set sqlalchemy.url from settings.SYNC_DATABASE_URL
    (or fallback to DATABASE_URL with +asyncpg removed).
    """
    project_root = Path(__file__).resolve().parents[2]  # adjust if needed
    if not alembic_ini_path:
        alembic_ini_path = os.path.join(project_root, "alembic.ini")

    cfg = Config(alembic_ini_path)

    # Prefer SYNC_DATABASE_URL (already computed by your Settings validators).
    sync_url = getattr(settings, "SYNC_DATABASE_URL", None)
    if not sync_url:
        # fallback: remove +asyncpg if present
        db_url = getattr(settings, "DATABASE_URL", None)
        if db_url:
            sync_url = db_url.replace("+asyncpg", "")
    if sync_url:
        cfg.set_main_option("sqlalchemy.url", sync_url)

    # ensure script_location configured (optional)
    if not cfg.get_main_option("script_location"):
        cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))

    return cfg

def run_migrations() -> None:
    """
    Run alembic upgrade head programmatically.
    """
    cfg = get_alembic_config()
    command.upgrade(cfg, "head")
