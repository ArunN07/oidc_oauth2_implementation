"""Authentication Models Package."""

from src.fastapi.models.auth.azure_models import AzureLoginResponse, AzureUser, AzureUserResponse
from src.fastapi.models.auth.common_models import AuthResponse, RoleCheckResponse, UnifiedUser
from src.fastapi.models.auth.github_models import GitHubEmail, GitHubLoginResponse, GitHubUser, GitHubUserResponse
from src.fastapi.models.auth.google_models import GoogleLoginResponse, GoogleUser, GoogleUserResponse

__all__ = [
    # Azure
    "AzureLoginResponse",
    "AzureUser",
    "AzureUserResponse",
    # Common
    "AuthResponse",
    "RoleCheckResponse",
    "UnifiedUser",
    # GitHub
    "GitHubEmail",
    "GitHubLoginResponse",
    "GitHubUser",
    "GitHubUserResponse",
    # Google
    "GoogleLoginResponse",
    "GoogleUser",
    "GoogleUserResponse",
]
