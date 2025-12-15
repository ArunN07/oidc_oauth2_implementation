"""
Custom Logger Configuration.

This module provides logging configuration and utilities for the application
including file and console handlers with proper formatting.
"""

import logging
import sys
from logging.config import dictConfig
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_LOG_FILE = str(PROJECT_ROOT / "logs" / "app.log")


def get_logging_config(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    handlers_to_use: list | None = None,
) -> dict:
    """
    Returns a logging configuration dictionary for use with dictConfig.

    Parameters
    ----------
    log_level : int
        The logging level (default is logging.INFO).
    log_file : str
        The file path for the file handler.
    handlers_to_use : list, optional
        List of handlers to use ("console", "file").

    Returns
    -------
    dict
        Logging configuration dictionary.
    """
    if handlers_to_use is None:
        handlers_to_use = ["console", "file"]

    if log_file is None:
        log_file = DEFAULT_LOG_FILE

    handlers_config = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": log_level,
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "detailed",
            "level": log_level,
            "filename": log_file,
        },
    }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
            "detailed": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"},
        },
        "handlers": {handler: handlers_config[handler] for handler in handlers_to_use if handler in handlers_config},
        "loggers": {
            "app_logger": {
                "handlers": [h for h in handlers_to_use if h in handlers_config],
                "level": log_level,
                "propagate": False,
            }
        },
    }

    return config


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    handlers_to_use: list | None = None,
) -> None:
    """
    Configure logging using dictConfig.

    Parameters
    ----------
    log_level : int
        The logging level.
    log_file : str
        The file path for logs.
    handlers_to_use : list, optional
        Handlers to enable.
    """
    if handlers_to_use is None:
        handlers_to_use = ["console", "file"]

    config = get_logging_config(log_level, log_file, handlers_to_use)
    dictConfig(config)


class CustomLogger:
    """
    Custom logger class for application-wide logging.

    Provides a configured logger instance with console and file handlers.
    """

    def __init__(
        self,
        logger_name: str = "app_logger",
        log_level: int = logging.INFO,
        log_file: str | None = None,
        handlers_to_use: list | None = None,
    ):
        """
        Initialize the custom logger.

        Parameters
        ----------
        logger_name : str
            Name of the logger.
        log_level : int
            Logging level.
        log_file : str
            File path for logs.
        handlers_to_use : list, optional
            List of handlers to use.
        """
        if handlers_to_use is None:
            handlers_to_use = ["console", "file"]

        self.logger_name = logger_name
        self.log_level = log_level
        self.log_file = log_file
        self.handlers_to_use = handlers_to_use
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on settings."""
        setup_logging(log_level=self.log_level, log_file=self.log_file, handlers_to_use=self.handlers_to_use)

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        Returns
        -------
        logging.Logger
            Configured logger.
        """
        return logging.getLogger(self.logger_name)
