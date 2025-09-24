# app/core/logger.py
import logging
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Remove default logger
logger.remove()

# Console logger
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO"
)

# File logger (production)
if settings.ENVIRONMENT == "production":
    logger.add(
        Path("logs") / "app.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO"
    )