"""
Azure AD OAuth2/OIDC Authentication Service.

This module provides Azure Active Directory authentication support for both
OAuth2 and OIDC flows with PKCE and refresh token support.
"""

import secrets
from typing import Any, cast

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.http_client import get_http_client
from src.core.auth.oidc_client import GenericOIDCClient
from src.core.auth.oidc_token_validator import OIDCTokenValidator
from src.core.settings.app import get_settings


class AzureAuthService(BaseAuthProvider):
    """
    Azure AD OIDC authentication service with refresh_token support.

    Notes
    -----
    To get refresh_token from Azure AD:
    1. Scope must include 'offline_access'
    2. prompt=consent is used to ensure user grants offline access
    """

    def __init__(self) -> None:
        """Initialize Azure AD OIDC client and token validator."""
        self.settings = get_settings()

        self.proxy = None
        if not self.settings.disable_proxy:
            self.proxy = self.settings.https_proxy or self.settings.http_proxy

        scopes = self.settings.azure_scopes
        if "offline_access" not in scopes:
            scopes = f"{scopes} offline_access"

        self._client = GenericOIDCClient(
            client_id=self.settings.azure_client_id,
            client_secret=self.settings.azure_client_secret,
            redirect_uri=self.settings.azure_redirect_uri,
            token_endpoint=self.settings.azure_token_url,
            authorization_endpoint=self.settings.azure_authorization_url,
            scope=scopes,
            use_pkce=True,
            proxy=self.proxy,
        )

        self._validator = OIDCTokenValidator(
            issuer=self.settings.azure_issuer,
            audience=self.settings.azure_client_id,
            jwks_uri=self.settings.azure_jwks_uri,
            proxy=self.proxy,
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "azure"

    @property
    def client(self) -> GenericOIDCClient:
        """Return the OIDC client instance."""
        return cast(GenericOIDCClient, self._client)

    @property
    def validator(self) -> OIDCTokenValidator:
        """Return the token validator instance."""
        return cast(OIDCTokenValidator, self._validator)

    def get_authorization_url(self, state: str | None = None) -> str:
        """Build authorization URL with prompt=consent for refresh_token."""
        state = state or secrets.token_hex(16)
        auth_url, _ = self._client.build_login_redirect_url(state=state, prompt="consent")
        return cast(str, auth_url)

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        return cast(dict[str, Any], await self._client.exchange_code_for_token(code, state=state))

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from Microsoft Graph API."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with get_http_client(proxy=self.proxy) as client:
            response = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """Validate id_token using JWKS."""
        return cast(dict[str, Any], await self._validator.validate_token(id_token))

    def decode_id_token(self, id_token: str) -> dict[str, Any]:
        """Decode id_token without validation."""
        return cast(dict[str, Any], self._validator.decode_token_unverified(id_token))

    async def get_user_from_token(self, token_response: dict[str, Any]) -> dict[str, Any]:
        """Extract user info from id_token claims."""
        id_token = token_response.get("id_token")
        if id_token:
            claims = self.decode_id_token(id_token)
            return {
                "sub": claims.get("sub", ""),
                "name": claims.get("name"),
                "preferred_username": claims.get("preferred_username"),
                "email": claims.get("email") or claims.get("preferred_username"),
                "oid": claims.get("oid"),
                "tid": claims.get("tid"),
                "groups": claims.get("groups", []),
                "claims": claims,
            }
        return {}

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token."""
        return cast(dict[str, Any], await self._client.refresh_token(refresh_token))


register_provider("azure", AzureAuthService)
