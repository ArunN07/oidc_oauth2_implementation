"""
Authorization Utilities for FastAPI.

This module provides authentication and authorization dependencies for
FastAPI endpoints including bearer token validation and role-based access.
"""

from logging import Logger
from typing import Any, Callable, Literal

from fastapi import Depends, Header, HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import get_auth_provider
from src.core.auth.security import bearer_scheme
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import ProviderNotSupportedError
from src.core.settings.app import AuthProvider, get_settings

# Create Literal type from AuthProvider enum values for dropdown in API docs
# Note: These values must match AuthProvider enum values
ProviderLiteral = Literal["github", "azure", "google", "okta", "facebook"]

# Validate that ProviderLiteral values match AuthProvider enum at runtime
_VALID_PROVIDERS = {p.value for p in AuthProvider}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    provider: ProviderLiteral | None = Query(None, description="Auth provider override"),
    logger: Logger = Depends(get_logger),
) -> dict[str, Any]:
    """
    Get current authenticated user from the access token.

    This is the main authentication dependency that validates tokens
    and retrieves user information from the configured provider.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials
        Bearer token from Authorization header.
    provider : str, optional
        Override auth provider ('github', 'azure', 'google').
    logger : Logger
        Logger instance for logging.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - provider: str - The provider name
        - user: dict - User information from provider
        - access_token: str - The access token

    Raises
    ------
    HTTPException
        401 if token is missing or invalid.
        400 if provider is not supported.
    HTTPException
        If token is missing or invalid.
    """
    if not credentials:
        logger.warning("Missing authentication credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = credentials.credentials

    try:
        auth_service = get_auth_provider(provider=provider)
        user_info = await auth_service.get_user_info(access_token)

        logger.info("Authenticated user via %s", auth_service.provider_name)

        return {
            "provider": auth_service.provider_name,
            "user": user_info,
            "access_token": access_token,
        }
    except ProviderNotSupportedError as e:
        logger.error("Provider not supported: %s", e.provider)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Authentication failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def authorize_user_access(required_roles: list[str] | None = None) -> Callable:
    """
    Factory function to create authorization dependency.

    Similar to project_authorization.py pattern - returns a callable
    dependency that validates user access and roles.

    Parameters
    ----------
    required_roles : list[str], optional
        List of required roles (e.g., ['admin'], ['user', 'moderator']).

    Returns
    -------
    Callable
        FastAPI dependency function validating user access.
        Returns a dict with 'user' and 'provider' keys.

    Example
    -------
    ```python
    @router.get("/admin")
    async def admin_endpoint(
        auth_context: dict = Depends(authorize_user_access(required_roles=["admin"]))
    ):
        user = auth_context["user"]
        return {"message": f"Hello admin {user.get('name')}"}
    ```
    """

    async def dependency(
        current_user: dict[str, Any] = Security(get_current_user),
        logger: Logger = Depends(get_logger),
    ) -> dict[str, Any]:
        user = current_user.get("user", {})
        provider = current_user.get("provider", "unknown")

        # If roles are required, validate them
        if required_roles:
            user_roles = _extract_user_roles(user, provider)

            if not any(role in user_roles for role in required_roles):
                logger.warning("User lacks required roles. Has: %s, Needs: %s", user_roles, required_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required role. Required: {required_roles}",
                )

        return {
            "user": user,
            "provider": provider,
            "access_token": current_user.get("access_token"),
        }

    return dependency


def _extract_user_roles(user: dict[str, Any], provider: str) -> list[str]:
    """
    Extract user roles based on provider and admin configuration.

    Parameters
    ----------
    user : Dict[str, Any]
        User information from provider.
    provider : str
        Provider name.

    Returns
    -------
    list[str]
        List of user roles.
    """
    settings = get_settings()
    roles = ["user"]  # Default role

    if provider == "github":
        username = user.get("login", "")
        # Check if user is admin based on env config
        admin_usernames = getattr(settings, "github_admin_usernames", "").split(",")
        if username in [u.strip() for u in admin_usernames if u.strip()]:
            roles.append("admin")

    elif provider == "google":
        email = user.get("email", "")
        # Check if user is admin based on env config
        admin_emails = getattr(settings, "google_admin_emails", "").split(",")
        if email in [e.strip() for e in admin_emails if e.strip()]:
            roles.append("admin")

    elif provider == "azure":
        # Azure can have roles in the token claims
        azure_roles = user.get("roles", [])
        roles.extend(azure_roles)

    return roles


def get_provider_dependency(
    provider: ProviderLiteral | None = Query(None, description="Override auth provider (github, azure, google)"),
    logger: Logger = Depends(get_logger),
) -> BaseAuthProvider:
    """
    FastAPI dependency for getting the auth provider service.

    Can be overridden via query parameter or uses .env default.

    Parameters
    ----------
    provider : str, optional
        Provider override via query parameter.
    logger : Logger
        Logger instance.

    Returns
    -------
    BaseAuthProvider
        The authentication provider service.
    """
    try:
        auth_provider = get_auth_provider(provider=provider)
        logger.info("Using auth provider: %s", auth_provider.provider_name)
        return auth_provider
    except ProviderNotSupportedError as e:
        logger.error("Provider not supported: %s", e.provider)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


def get_active_provider_name() -> str:
    """
    Get the name of the active provider from settings.

    Returns
    -------
    str
        Provider name.
    """
    return get_settings().auth_provider.value


def validate_access_token(
    authorization: str = Header(..., description="Bearer token"),
    logger: Logger = Depends(get_logger),
) -> str:
    """
    Simple dependency to extract and validate access token format.

    Parameters
    ----------
    authorization : str
        Authorization header value.
    logger : Logger
        Logger instance.

    Returns
    -------
    str
        The access token.
    """
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")
    if not token:
        logger.warning("Empty access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


class AuthDependency:
    """
    Configurable authentication dependency class.

    Allows creating auth dependencies with specific providers.
    """

    def __init__(self, provider: str | None = None):
        """
        Initialize auth dependency.

        Parameters
        ----------
        provider : str, optional
            Fixed provider to use. If None, uses settings default.
        """
        self.provider = provider

    def __call__(self, logger: Logger = Depends(get_logger)) -> BaseAuthProvider:
        """
        Get the auth provider.

        Parameters
        ----------
        logger : Logger
            Logger instance.

        Returns
        -------
        BaseAuthProvider
            The authentication provider.
        """
        try:
            return get_auth_provider(provider=self.provider)
        except ProviderNotSupportedError as e:
            logger.error("Provider not supported: %s", e.provider)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# Pre-configured dependencies for specific providers
github_auth = AuthDependency(provider="github")
azure_auth = AuthDependency(provider="azure")
google_auth = AuthDependency(provider="google")
