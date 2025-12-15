"""
Role Assignment Service.

This module provides role-based access control (RBAC) by assigning roles
to users based on their provider and configuration in environment variables.
"""

from enum import Enum
from typing import Any

from src.core.settings.app import get_settings


class Role(str, Enum):
    """User roles."""

    USER = "user"
    ADMIN = "admin"


class RoleService:
    """Assigns roles based on .env configuration."""

    _instance: "RoleService | None" = None
    _initialized: bool = False

    def __new__(cls) -> "RoleService":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize role service with settings."""
        if self._initialized:
            return
        self.settings = get_settings()
        RoleService._initialized = True

    def get_user_roles(self, provider: str, user_data: dict[str, Any]) -> list[str]:
        """Get roles for user based on provider and .env config."""
        roles = [Role.USER.value]

        match provider:
            case "github":
                roles.extend(self._get_github_roles(user_data))
            case "azure":
                roles.extend(self._get_azure_roles(user_data))
            case "google":
                roles.extend(self._get_google_roles(user_data))

        return list(set(roles))

    def get_user_groups(self, provider: str, user_data: dict[str, Any]) -> list[str]:
        """Get groups/organizations for user."""
        match provider:
            case "github":
                return list(user_data.get("organizations", []))
            case "azure":
                claims = user_data.get("claims", {})
                return list(claims.get("groups", []))
            case "google":
                email = user_data.get("email", "")
                domain = email.split("@")[-1] if "@" in email else ""
                return [domain] if domain else []
            case _:
                return []

    def _get_github_roles(self, user_data: dict[str, Any]) -> list[str]:
        """Check GitHub admin roles."""
        roles = []
        username = user_data.get("login", "")
        orgs = user_data.get("organizations", [])

        admin_usernames = self._parse_csv(self.settings.github_admin_usernames)
        if username in admin_usernames:
            roles.append(Role.ADMIN.value)

        admin_orgs = self._parse_csv(self.settings.github_admin_orgs)
        if any(org in admin_orgs for org in orgs):
            roles.append(Role.ADMIN.value)

        return roles

    def _get_azure_roles(self, user_data: dict[str, Any]) -> list[str]:
        """Check Azure admin roles."""
        roles = []
        email = user_data.get("email", "") or user_data.get("preferred_username", "")

        admin_usernames = self._parse_csv(self.settings.azure_admin_usernames)
        if email in admin_usernames:
            roles.append(Role.ADMIN.value)

        admin_groups = self._parse_csv(self.settings.azure_admin_groups)
        user_groups = user_data.get("groups", [])
        if any(g in admin_groups for g in user_groups):
            roles.append(Role.ADMIN.value)

        return roles

    def _get_google_roles(self, user_data: dict[str, Any]) -> list[str]:
        """Check Google admin roles."""
        roles = []
        email = user_data.get("email", "")

        admin_emails = self._parse_csv(self.settings.google_admin_emails)
        if email in admin_emails:
            roles.append(Role.ADMIN.value)

        domain = email.split("@")[-1] if "@" in email else ""
        admin_domains = self._parse_csv(self.settings.google_admin_domains)
        if domain in admin_domains:
            roles.append(Role.ADMIN.value)

        return roles

    def _parse_csv(self, value: str) -> list[str]:
        """Parse comma-separated values into list."""
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]


def get_role_service() -> RoleService:
    """Get role service singleton."""
    return RoleService()
