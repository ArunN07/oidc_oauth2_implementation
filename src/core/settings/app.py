import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path

from environs import Env
from pydantic import Field
from pydantic_settings import BaseSettings

# Project root directory (4 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Load environment early for configuration
_env = Env()
_env.read_env(recurse=True, override=True)


class AppEnvTypes(str, Enum):
    """
    Application environment types.

    Attributes
    ----------
    PROD : str
        Production environment.
    DEV : str
        Development environment.
    TEST : str
        Testing environment.
    """

    PROD = "prod"
    PRODUCTION = "production"
    DEV = "dev"
    DEVELOPMENT = "development"
    TEST = "test"


class AuthProvider(str, Enum):
    """
    Supported authentication providers.

    Attributes
    ----------
    GITHUB : str
        GitHub OAuth2 provider.
    AZURE : str
        Microsoft Azure AD provider.
    GOOGLE : str
        Google OAuth2/OIDC provider.
    OKTA : str
        Okta OIDC provider (planned).
    FACEBOOK : str
        Facebook OAuth2 provider (planned).
    """

    GITHUB = "github"
    AZURE = "azure"
    GOOGLE = "google"
    OKTA = "okta"
    FACEBOOK = "facebook"


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    All OAuth2/OIDC provider configurations are centralized here.
    Settings are loaded from .env file and environment variables.

    Attributes
    ----------
    app_env : AppEnvTypes
        Current application environment.
    debug : bool
        Enable debug mode.
    auth_provider : AuthProvider
        Default authentication provider.
    github_client_id : str
        GitHub OAuth2 client ID.
    azure_tenant_id : str
        Azure AD tenant ID.
    google_client_id : str
        Google OAuth2 client ID.
    """

    # Application Settings
    app_env: AppEnvTypes = Field(default=AppEnvTypes.DEV, alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    title: str = Field(default="OIDC OAuth2 Demo", alias="APP_TITLE")
    description: str = Field(default="FastAPI OIDC/OAuth2 Authentication Demo", alias="APP_DESCRIPTION")
    version: str = Field(default="1.0.0", alias="APP_VERSION")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # Logging Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(
        default=str(PROJECT_ROOT / "logs" / "app.log"),
        alias="LOG_FILE"
    )

    # Auth Provider Switch
    auth_provider: AuthProvider = Field(default=AuthProvider.GITHUB, alias="AUTH_PROVIDER")

    # GitHub OAuth2 Configuration
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(
        default="http://localhost:8001/api/v1/auth/github/callback", alias="GITHUB_REDIRECT_URI"
    )
    github_authorization_url: str = Field(
        default="https://github.com/login/oauth/authorize", alias="GITHUB_AUTHORIZATION_URL"
    )
    github_token_url: str = Field(default="https://github.com/login/oauth/access_token", alias="GITHUB_TOKEN_URL")
    github_user_api_url: str = Field(default="https://api.github.com/user", alias="GITHUB_USER_API_URL")
    github_scopes: str = Field(default="read:user user:email", alias="GITHUB_SCOPES")
    github_admin_usernames: str = Field(default="", alias="GITHUB_ADMIN_USERNAMES")
    github_admin_orgs: str = Field(default="", alias="GITHUB_ADMIN_ORGS")

    # Azure AD OAuth2/OIDC Configuration
    azure_tenant_id: str = Field(default="", alias="AZURE_TENANT_ID")
    azure_client_id: str = Field(default="", alias="AZURE_CLIENT_ID")
    azure_client_secret: str = Field(default="", alias="AZURE_CLIENT_SECRET")
    azure_redirect_uri: str = Field(
        default="http://localhost:8001/api/v1/auth/azure/callback", alias="AZURE_REDIRECT_URI"
    )
    azure_scopes: str = Field(default="openid profile email offline_access", alias="AZURE_SCOPES")
    azure_admin_usernames: str = Field(default="", alias="AZURE_ADMIN_USERNAMES")
    azure_admin_groups: str = Field(default="", alias="AZURE_ADMIN_GROUPS")
    azure_admin_domains: str = Field(default="", alias="AZURE_ADMIN_DOMAINS")

    # Google OAuth2/OIDC Configuration
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8001/api/v1/auth/google/callback", alias="GOOGLE_REDIRECT_URI"
    )
    google_authorization_url: str = Field(
        default="https://accounts.google.com/o/oauth2/v2/auth", alias="GOOGLE_AUTHORIZATION_URL"
    )
    google_token_url: str = Field(default="https://oauth2.googleapis.com/token", alias="GOOGLE_TOKEN_URL")
    google_jwks_uri: str = Field(default="https://www.googleapis.com/oauth2/v3/certs", alias="GOOGLE_JWKS_URI")
    google_issuer: str = Field(default="https://accounts.google.com", alias="GOOGLE_ISSUER")
    google_user_info_url: str = Field(
        default="https://www.googleapis.com/oauth2/v3/userinfo", alias="GOOGLE_USER_INFO_URL"
    )
    google_scopes: str = Field(default="openid profile email", alias="GOOGLE_SCOPES")
    google_admin_emails: str = Field(default="", alias="GOOGLE_ADMIN_EMAILS")
    google_admin_domains: str = Field(default="", alias="GOOGLE_ADMIN_DOMAINS")
    google_allowed_domains: str = Field(default="", alias="GOOGLE_ALLOWED_DOMAINS")

    # Database Configuration
    database_type: str = Field(default="postgresql", alias="DATABASE_TYPE")
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    database_name: str = Field(default="oidc_demo", alias="DATABASE_NAME")
    database_user: str = Field(default="postgres", alias="DATABASE_USER")
    database_password: str = Field(default="postgres", alias="DATABASE_PASSWORD")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Proxy Settings
    http_proxy: str | None = Field(default=None, alias="HTTP_PROXY")
    https_proxy: str | None = Field(default=None, alias="HTTPS_PROXY")
    disable_proxy: bool = Field(default=True, alias="DISABLE_PROXY")

    # Security Settings
    secret_key: str = Field(default="your-super-secret-key-change-in-production", alias="SECRET_KEY")
    session_expire_minutes: int = Field(default=60, alias="SESSION_EXPIRE_MINUTES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def logging_level(self) -> int:
        """Convert string log level to logging constant."""
        return getattr(logging, self.log_level.upper(), logging.INFO)

    @property
    def azure_authorization_url(self) -> str:
        """Generate Azure authorization URL from tenant ID."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/authorize"

    @property
    def azure_token_url(self) -> str:
        """Generate Azure token URL from tenant ID."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/token"

    @property
    def azure_jwks_uri(self) -> str:
        """Generate Azure JWKS URI from tenant ID."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/discovery/v2.0/keys"

    @property
    def azure_issuer(self) -> str:
        """Generate Azure issuer from tenant ID."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/v2.0"

    def get_database_url(self) -> str:
        """Build database URL from components or return configured URL."""
        if self.database_url:
            return self.database_url
        return (
            f"{self.database_type}://{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns
    -------
    Settings
        Application settings instance.
    """
    return Settings()


def create_app_settings() -> Settings:
    """
    Create a new settings instance (useful for testing).

    Returns
    -------
    Settings
        New application settings instance.
    """
    return Settings()


# Global settings instance for backward compatibility
settings = get_settings()
