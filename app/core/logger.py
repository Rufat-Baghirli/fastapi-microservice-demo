# app/core/logger.py
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Remove default loguru handlers (avoid duplicate logs)
logger.remove()

# Console logger (useful for dev & container logs)
logger.add(
    sink=lambda msg: print(msg, end=""),  # portable fallback, but we can also use sys.stderr
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    enqueue=True,  # safe for multi-thread/process
)

# If running in production, ensure logs directory exists and add file logger
if settings.ENVIRONMENT == "production":
    logs_dir = Path("logs")
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # If creating the directory fails, still keep console logging but log the issue
        logger.warning("Unable to create logs directory: {}", e)
    else:
        logger.add(
            logs_dir / "app.log",
            rotation="10 MB",       # rotate after 10 MB
            retention="10 days",    # keep logs for 10 days
            level="INFO",
            enqueue=True,          # safe write across processes
            backtrace=True,        # show python backtrace
            diagnose=False,        # avoid huge diagnostics in production unless needed
        )
