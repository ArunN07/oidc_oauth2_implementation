"""Authentication Services Package."""

from src.fastapi.services.auth.azure_service import AzureAuthService
from src.fastapi.services.auth.github_service import GitHubAuthService
from src.fastapi.services.auth.google_service import GoogleAuthService
from src.fastapi.services.auth.role_service import Role, RoleService, get_role_service

__all__ = [
    "AzureAuthService",
    "GitHubAuthService",
    "GoogleAuthService",
    "Role",
    "RoleService",
    "get_role_service",
]
