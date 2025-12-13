"""Google OAuth2/OIDC authentication service."""

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.oidc_client import GenericOIDCClient, _generate_pkce_pair
from src.core.auth.oidc_token_validator import OIDCTokenValidator
from src.core.auth.pkce_store import get_pkce_store
from src.core.settings.app import get_settings


class GoogleAuthService(BaseAuthProvider):
    """Google OIDC authentication service with refresh_token support."""

    def __init__(self):
        """Initialize Google OIDC client and token validator."""
        self.settings = get_settings()

        proxy = None
        if not self.settings.disable_proxy:
            proxy = self.settings.https_proxy or self.settings.http_proxy

        self._client = GenericOIDCClient(
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            redirect_uri=self.settings.google_redirect_uri,
            token_endpoint=self.settings.google_token_url,
            authorization_endpoint=self.settings.google_authorization_url,
            scope=self.settings.google_scopes,
            user_info_endpoint=self.settings.google_user_info_url,
            use_pkce=True,
        )

        self._validator = OIDCTokenValidator(
            issuer=self.settings.google_issuer,
            audience=self.settings.google_client_id,
            jwks_uri=self.settings.google_jwks_uri,
            proxy=proxy,
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

        code_verifier, code_challenge = _generate_pkce_pair()
        get_pkce_store().store(state, code_verifier)

        params = {
            "client_id": self.settings.google_client_id,
            "response_type": "code",
            "redirect_uri": self.settings.google_redirect_uri,
            "scope": self.settings.google_scopes,
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.settings.google_authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        code_verifier = get_pkce_store().retrieve(state) if state else None

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": self.settings.google_redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.settings.google_token_url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

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
