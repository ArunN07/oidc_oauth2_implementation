"""Google OAuth2/OIDC authentication service."""

import secrets
from typing import Any

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.oidc_client import GenericOIDCClient
from src.core.auth.oidc_token_validator import OIDCTokenValidator
from src.core.settings.app import get_settings


class GoogleAuthService(BaseAuthProvider):
    """Google OIDC authentication service with refresh_token support."""

    def __init__(self):
        """Initialize Google OIDC client and token validator."""
        self.settings = get_settings()

        self.proxy = None
        if not self.settings.disable_proxy:
            self.proxy = self.settings.https_proxy or self.settings.http_proxy

        self._client = GenericOIDCClient(
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            redirect_uri=self.settings.google_redirect_uri,
            token_endpoint=self.settings.google_token_url,
            authorization_endpoint=self.settings.google_authorization_url,
            scope=self.settings.google_scopes,
            user_info_endpoint=self.settings.google_user_info_url,
            use_pkce=True,
            proxy=self.proxy,
        )

        self._validator = OIDCTokenValidator(
            issuer=self.settings.google_issuer,
            audience=self.settings.google_client_id,
            jwks_uri=self.settings.google_jwks_uri,
            proxy=self.proxy,
        )

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def client(self) -> GenericOIDCClient:
        return self._client

    @property
    def validator(self) -> OIDCTokenValidator:
        return self._validator

    def get_authorization_url(self, state: str | None = None) -> str:
        """Build authorization URL with access_type=offline for refresh_token."""
        state = state or secrets.token_hex(16)
        # Use GenericOIDCClient with extra_params for Google-specific options
        auth_url, _ = self._client.build_login_redirect_url(
            state=state,
            prompt="consent",
            extra_params={"access_type": "offline"},
        )
        return auth_url

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        return await self._client.exchange_code_for_token(code, state=state)

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """Validate id_token using JWKS."""
        return await self._validator.validate_token(id_token)

    def decode_id_token(self, id_token: str) -> dict[str, Any]:
        """Decode id_token without validation."""
        return self._validator.decode_token_unverified(id_token)

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from Google userinfo endpoint."""
        return await self._client.get_user_info(access_token)

    async def get_user_from_token(self, token_response: dict[str, Any]) -> dict[str, Any]:
        """Extract user info from id_token claims."""
        id_token = token_response.get("id_token")
        if id_token:
            claims = self.decode_id_token(id_token)
            return {
                "sub": claims.get("sub", ""),
                "name": claims.get("name"),
                "email": claims.get("email"),
                "email_verified": claims.get("email_verified"),
                "picture": claims.get("picture"),
                "claims": claims,
            }
        return {}

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token."""
        return await self._client.refresh_token(refresh_token)


register_provider("google", GoogleAuthService)
