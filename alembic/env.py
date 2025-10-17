from logging.config import fileConfig
import os
import sys
import asyncio
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

sys.path.append(os.path.abspath("."))

# Import the global settings object directly
from app.core.config import settings

# Import the Base model
from app.models.base import Base
# Import all models to ensure they are registered with Base.metadata
try:
    import app.models.user
except Exception:
    pass

target_metadata = Base.metadata

config = context.config
fileConfig(config.config_file_name)

# Use the SYNC_DATABASE_URL from settings
if not config.get_main_option("sqlalchemy.url"):
    try:
        config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)
    except Exception:
        # fallback to env var if settings.SYNC_DATABASE_URL is not set
        cfg_url = os.getenv("DATABASE_URL", "")
        if cfg_url:
            config.set_main_option("sqlalchemy.url", cfg_url.replace("+asyncpg", ""))

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_sync():
    from sqlalchemy import engine_from_config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)

async def run_migrations_async():
    from sqlalchemy.ext.asyncio import create_async_engine
    async_url = settings.DATABASE_URL
    connectable = create_async_engine(async_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def main():
    original_url = settings.DATABASE_URL or os.getenv("DATABASE_URL", "")
    is_async = "+asyncpg" in original_url or original_url.startswith("sqlite+aiosqlite")

    if is_async:
        asyncio.run(run_migrations_async())
    else:
        run_migrations_sync()

if context.is_offline_mode():
    run_migrations_offline()
else:
    main()