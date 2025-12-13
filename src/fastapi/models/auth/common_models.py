from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UnifiedUser(BaseModel):
    """
    Unified user model across all OAuth providers.

    Normalizes user info from GitHub, Azure, Google into a standard format.
    """

    id: str = Field(..., description="Unique user ID from provider")
    provider: str = Field(..., description="OAuth provider name")
    username: Optional[str] = Field(None, description="Username/login")
    email: Optional[str] = Field(None, description="Primary email")
    name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    roles: List[str] = Field(default_factory=lambda: ["user"], description="User roles")
    groups: List[str] = Field(default_factory=list, description="Organizations/Groups")
    raw_info: Dict[str, Any] = Field(default_factory=dict, description="Original provider data")

    @classmethod
    def from_github(
        cls, user_info: Dict[str, Any], roles: List[str], groups: Optional[List[str]] = None
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
            groups=groups or user_info.get("organizations", []),
            raw_info=user_info,
        )

    @classmethod
    def from_azure(
        cls, user_info: Dict[str, Any], roles: List[str], groups: Optional[List[str]] = None
    ) -> "UnifiedUser":
        """Create UnifiedUser from Azure AD user info."""
        return cls(
            id=str(user_info.get("id", user_info.get("sub", ""))),
            provider="azure",
            username=user_info.get("userPrincipalName"),
            email=user_info.get("mail") or user_info.get("userPrincipalName"),
            name=user_info.get("displayName") or user_info.get("name"),
            avatar_url=None,  # Azure doesn't return avatar in basic profile
            roles=roles,
            groups=groups or user_info.get("groups", []),
            raw_info=user_info,
        )

    @classmethod
    def from_google(
        cls, user_info: Dict[str, Any], roles: List[str], groups: Optional[List[str]] = None
    ) -> "UnifiedUser":
        """Create UnifiedUser from Google user info."""
        email = user_info.get("email", "")
        domain = email.split("@")[1] if "@" in email else None
        return cls(
            id=str(user_info.get("sub", user_info.get("id", ""))),
            provider="google",
            username=email.split("@")[0] if email else None,
            email=email,
            name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
            roles=roles,
            groups=groups or ([domain] if domain else []),
            raw_info=user_info,
        )

    @classmethod
    def from_provider(
        cls,
        provider: str,
        user_info: Dict[str, Any],
        roles: List[str],
        groups: Optional[List[str]] = None,
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
                groups=groups or [],
                raw_info=user_info,
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
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class RoleCheckResponse(BaseModel):
    """Response for role check endpoints."""

    user_id: str
    provider: str
    roles: List[str]
    is_admin: bool
