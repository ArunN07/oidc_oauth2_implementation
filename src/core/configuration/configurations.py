"""
Provider configuration management for OAuth2/OIDC authentication.

This module provides centralized configuration for OAuth2/OIDC providers.
It encapsulates all provider-specific settings (endpoints, credentials,
scopes) in a unified ProviderConfig dataclass.

Why ProviderConfig?
------------------
ProviderConfig provides several benefits:
1. **Type Safety**: All configuration is typed and validated
2. **Centralization**: All provider settings in one place
3. **Consistency**: Same interface for all providers
4. **Easy Testing**: Mock configurations for tests

Configuration Sources:
---------------------
All values come from environment variables via the Settings class:
- GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, etc.
- AZURE_CLIENT_ID, AZURE_TENANT_ID, etc.
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, etc.

Classes
-------
ProviderConfig
    Dataclass containing all provider configuration.
ProviderEndpoints
    Static methods for getting provider-specific configs.

Functions
---------
get_provider_config
    Get configuration for a specific provider.
get_active_provider
    Get the currently active provider from settings.
get_active_provider_config
    Get configuration for the active provider.

Examples
--------
Getting configuration for a specific provider:

>>> from src.core.configuration.configurations import get_provider_config
>>> from src.core.settings.app import AuthProvider
>>>
>>> config = get_provider_config(AuthProvider.GITHUB)
>>> print(config.client_id)
>>> print(config.authorization_url)
"""

from dataclasses import dataclass

from src.core.settings.app import AuthProvider, get_settings


@dataclass
class ProviderConfig:
    """
    OAuth2/OIDC provider configuration.

    This dataclass contains all the configuration needed to interact with
    an OAuth2/OIDC provider. It includes credentials, endpoints, and scopes.

    Attributes
    ----------
    name : str
        Provider identifier ('github', 'azure', 'google').
    client_id : str
        OAuth2 client ID registered with the provider.
    client_secret : str
        OAuth2 client secret (keep confidential!).
    redirect_uri : str
        Callback URL registered with the provider.
    authorization_url : str
        Provider's authorization endpoint URL.
    token_url : str
        Provider's token exchange endpoint URL.
    scopes : str
        Space-separated list of OAuth2/OIDC scopes.
    user_info_url : str | None
        URL to fetch user info (OAuth2 providers, optional for OIDC).
    jwks_uri : str | None
        URL to fetch JWKS for JWT validation (OIDC only).
    issuer : str | None
        Expected token issuer for validation (OIDC only).

    Notes
    -----
    - GitHub (OAuth2): Has user_info_url, no jwks_uri/issuer
    - Azure/Google (OIDC): Have jwks_uri and issuer for JWT validation

    Examples
    --------
    >>> config = ProviderConfig(
    ...     name="github",
    ...     client_id="xxx",
    ...     client_secret="yyy",
    ...     redirect_uri="http://localhost:8000/callback",
    ...     authorization_url="https://github.com/login/oauth/authorize",
    ...     token_url="https://github.com/login/oauth/access_token",
    ...     scopes="read:user user:email",
    ...     user_info_url="https://api.github.com/user",
    ... )
    """

    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    scopes: str
    user_info_url: str | None = None
    jwks_uri: str | None = None
    issuer: str | None = None


class ProviderEndpoints:
    """
    Centralized provider endpoint configurations.

    Provides easy access to OAuth2/OIDC endpoints for all supported providers.
    """

    @staticmethod
    def get_github_config() -> ProviderConfig:
        """Get GitHub OAuth2 configuration."""
        settings = get_settings()
        return ProviderConfig(
            name="github",
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
            authorization_url=settings.github_authorization_url,
            token_url=settings.github_token_url,
            scopes=settings.github_scopes,
            user_info_url=settings.github_user_api_url,
        )

    @staticmethod
    def get_azure_config() -> ProviderConfig:
        """Get Azure AD OAuth2/OIDC configuration."""
        settings = get_settings()
        return ProviderConfig(
            name="azure",
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
            redirect_uri=settings.azure_redirect_uri,
            authorization_url=settings.azure_authorization_url,
            token_url=settings.azure_token_url,
            scopes=settings.azure_scopes,
            jwks_uri=settings.azure_jwks_uri,
            issuer=settings.azure_issuer,
        )

    @staticmethod
    def get_google_config() -> ProviderConfig:
        """Get Google OAuth2/OIDC configuration."""
        settings = get_settings()
        return ProviderConfig(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
            authorization_url=settings.google_authorization_url,
            token_url=settings.google_token_url,
            scopes=settings.google_scopes,
            user_info_url=settings.google_user_info_url,
            jwks_uri=settings.google_jwks_uri,
            issuer=settings.google_issuer,
        )


def get_provider_config(provider: AuthProvider) -> ProviderConfig:
    """
    Get configuration for a specific provider.

    Parameters
    ----------
    provider : AuthProvider
        The authentication provider.

    Returns
    -------
    ProviderConfig
        Configuration for the specified provider.

    Raises
    ------
    ValueError
        If provider is not supported.
    """
    config_map = {
        AuthProvider.GITHUB: ProviderEndpoints.get_github_config,
        AuthProvider.AZURE: ProviderEndpoints.get_azure_config,
        AuthProvider.GOOGLE: ProviderEndpoints.get_google_config,
    }

    if provider not in config_map:
        raise ValueError(f"Provider '{provider}' is not supported")

    return config_map[provider]()


def get_active_provider() -> AuthProvider:
    """
    Get the currently active authentication provider from settings.

    Returns
    -------
    AuthProvider
        The active authentication provider.
    """
    return get_settings().auth_provider


def get_active_provider_config() -> ProviderConfig:
    """
    Get configuration for the currently active provider.

    Returns
    -------
    ProviderConfig
        Configuration for the active provider.
    """
    return get_provider_config(get_active_provider())
