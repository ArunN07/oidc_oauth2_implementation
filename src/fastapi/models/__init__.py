"""FastAPI Models Package."""

from src.fastapi.models.auth.azure_models import (
    AzureCallbackResponse,
    AzureIdTokenClaims,
    AzureLoginResponse,
    AzureTokenResponse,
    AzureUser,
    AzureUserResponse,
)
from src.fastapi.models.auth.common_models import AuthResponse, RoleCheckResponse, UnifiedUser
from src.fastapi.models.auth.github_models import (
    GitHubCallbackResponse,
    GitHubEmail,
    GitHubLoginResponse,
    GitHubTokenResponse,
    GitHubUser,
    GitHubUserResponse,
)
from src.fastapi.models.auth.google_models import (
    GoogleCallbackResponse,
    GoogleIdTokenClaims,
    GoogleLoginResponse,
    GoogleTokenResponse,
    GoogleUser,
    GoogleUserResponse,
)
