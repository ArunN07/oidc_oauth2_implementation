"""FastAPI Utilities Package."""

from .authorization import (
    AuthDependency,
    authorize_user_access,
    azure_auth,
    bearer_scheme,
    get_active_provider_name,
    get_current_user,
    get_provider_dependency,
    github_auth,
    google_auth,
    validate_access_token,
)

__all__ = [
    "bearer_scheme",
    "get_current_user",
    "authorize_user_access",
    "get_provider_dependency",
    "get_active_provider_name",
    "validate_access_token",
    "AuthDependency",
    "github_auth",
    "azure_auth",
    "google_auth",
]
