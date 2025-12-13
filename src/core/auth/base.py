"""Base authentication provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAuthProvider(ABC):
    """Abstract base class for OAuth2/OIDC authentication providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name."""
        pass

    @abstractmethod
    def get_authorization_url(self, state: str | None = None) -> str:
        """Build the authorization URL for OAuth2 flow."""
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self, code: str, state: str | None = None
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user information using the access token."""
        pass

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token using a refresh token."""
        raise NotImplementedError(f"{self.provider_name} does not support token refresh")

    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate a token and return its payload."""
        raise NotImplementedError(f"{self.provider_name} does not support token validation")
