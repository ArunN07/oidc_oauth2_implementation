"""Core Exceptions Package."""

from src.core.exceptions.exceptions import (
    AuthError,
    BaseAppException,
    ConfigError,
    DatabaseConnectionError,
    DatabaseException,
    InvalidCredentialsError,
    MissingConfigurationError,
    OAuth2CallbackError,
    ProviderNotSupportedError,
    TokenExpiredError,
    TokenValidationError,
    UserNotFoundError,
)

__all__ = [
    "AuthError",
    "BaseAppException",
    "ConfigError",
    "DatabaseConnectionError",
    "DatabaseException",
    "InvalidCredentialsError",
    "MissingConfigurationError",
    "OAuth2CallbackError",
    "ProviderNotSupportedError",
    "TokenExpiredError",
    "TokenValidationError",
    "UserNotFoundError",
]
