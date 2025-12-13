from typing import Any

from pydantic import BaseModel, Field


class UnifiedUser(BaseModel):
    """
    Unified user model across all OAuth providers.

    Normalizes user info from GitHub, Azure, Google into a standard format.
    """

    id: str = Field(..., description="Unique user ID from provider")
    provider: str = Field(..., description="OAuth provider name")
    username: str | None = Field(None, description="Username/login")
    email: str | None = Field(None, description="Primary email")
    name: str | None = Field(None, description="Display name")
    avatar_url: str | None = Field(None, description="Profile picture URL")
    roles: list[str] = Field(default_factory=lambda: ["user"], description="User roles")

    @classmethod
    def from_github(
        cls, user_info: dict[str, Any], roles: list[str], groups: list[str] | None = None
    ) -> "UnifiedUser":
        """Create UnifiedUser from GitHub user info."""
        return cls(
            id=str(user_info.get("id", "")),
            provider="github",
            username=user_info.get("login"),
            email=user_info.get("email"),
            name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url"),
            roles=roles,
        )

    @classmethod
    def from_azure(
        cls, user_info: dict[str, Any], roles: list[str], groups: list[str] | None = None
    ) -> "UnifiedUser":
        """Create UnifiedUser from Azure AD user info."""
        return cls(
            id=str(user_info.get("id", user_info.get("sub", ""))),
            provider="azure",
            username=user_info.get("userPrincipalName"),
            email=user_info.get("mail") or user_info.get("userPrincipalName"),
            name=user_info.get("displayName") or user_info.get("name"),
            avatar_url=None,
            roles=roles,
        )

    @classmethod
    def from_google(
        cls, user_info: dict[str, Any], roles: list[str], groups: list[str] | None = None
    ) -> "UnifiedUser":
        """Create UnifiedUser from Google user info."""
        email = user_info.get("email", "")
        return cls(
            id=str(user_info.get("sub", user_info.get("id", ""))),
            provider="google",
            username=email.split("@")[0] if email else None,
            email=email,
            name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
            roles=roles,
        )

    @classmethod
    def from_provider(
        cls,
        provider: str,
        user_info: dict[str, Any],
        roles: list[str],
        groups: list[str] | None = None,
    ) -> "UnifiedUser":
        """Create UnifiedUser from any provider."""
        if provider == "github":
            return cls.from_github(user_info, roles, groups)
        elif provider == "azure":
            return cls.from_azure(user_info, roles, groups)
        elif provider == "google":
            return cls.from_google(user_info, roles, groups)
        else:
            # Generic fallback
            return cls(
                id=str(user_info.get("id", user_info.get("sub", "unknown"))),
                provider=provider,
                username=user_info.get("username") or user_info.get("login"),
                email=user_info.get("email"),
                name=user_info.get("name"),
                avatar_url=user_info.get("avatar_url") or user_info.get("picture"),
                roles=roles,
            )

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles or "super_admin" in self.roles

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles


class AuthResponse(BaseModel):
    """Standard auth response with unified user and tokens."""

    access_token: str
    token_type: str = "bearer"
    user: UnifiedUser
    id_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None


class RoleCheckResponse(BaseModel):
    """Response for role check endpoints."""

    user_id: str
    provider: str
    roles: list[str]
    is_admin: bool
