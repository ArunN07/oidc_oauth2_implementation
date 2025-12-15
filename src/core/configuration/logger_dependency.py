"""
Logger Dependency for FastAPI.

This module provides a FastAPI dependency for injecting configured loggers
into route handlers.
"""

import os
from logging import Logger

from src.core.configuration.custom_logger import CustomLogger
from src.core.settings.app import get_settings


def get_logger(log_level: int | None = None) -> Logger:
    """
    FastAPI dependency for getting a configured logger.

    Parameters
    ----------
    log_level : int, optional
        Override log level. Uses settings default if not provided.

    Returns
    -------
    Logger
        Configured logger instance.
    """
    settings = get_settings()

    # Ensure logs directory exists
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = CustomLogger(
        logger_name="app_logger",
        log_level=log_level or settings.logging_level,
        log_file=settings.log_file,
        handlers_to_use=["console", "file"],
    ).get_logger()

    return logger
