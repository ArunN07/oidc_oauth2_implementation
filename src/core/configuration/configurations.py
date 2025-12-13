from dataclasses import dataclass

from src.core.settings.app import AuthProvider, get_settings


@dataclass
class ProviderConfig:
    """OAuth2/OIDC Provider Configuration."""

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
