"""Core Package - Authentication, configuration, exceptions, and settings."""

from .auth import BaseAuthProvider, get_auth_provider
from .configuration import ProviderConfig, get_active_provider, get_logger
from .exceptions import AuthError, ConfigError, ProviderNotSupportedError
from .settings import AuthProvider, Settings, get_settings, settings

__all__ = [
    "Settings",
    "get_settings",
    "settings",
    "AuthProvider",
    "get_logger",
    "get_active_provider",
    "ProviderConfig",
    "AuthError",
    "ConfigError",
    "ProviderNotSupportedError",
    "BaseAuthProvider",
    "get_auth_provider",
]
