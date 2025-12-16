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
        """
        Get user info from Microsoft Graph API with groups.

        Note: For OAuth2 flow to retrieve groups, the access token needs one of:
        - GroupMember.Read.All scope (requires admin consent)
        - Directory.Read.All scope (requires admin consent)

        If groups cannot be fetched, we extract directory roles from the
        access token's 'wids' claim as a fallback.
        """
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        # Decode token to extract claims (for email and groups fallback)
        token_claims: dict[str, Any] = {}
        try:
            token_claims = self._validator.decode_token_unverified(access_token)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        async with get_http_client(proxy=self.proxy) as client:
            # Get basic user info
            response = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            response.raise_for_status()
            user_info = response.json()

            # Fallback: If Graph API doesn't return 'mail', use email from token claims
            # This is common for external/guest users (e.g., hotmail.com users in Azure AD)
            if not user_info.get("mail") and token_claims.get("email"):
                user_info["email"] = token_claims["email"]

            # Try to get user's group memberships
            groups: list[str] = []
            try:
                groups_response = await client.get("https://graph.microsoft.com/v1.0/me/memberOf", headers=headers)
                if groups_response.status_code == 200:
                    groups_data = groups_response.json()
                    # Extract group IDs from the response
                    groups = [group.get("id") for group in groups_data.get("value", []) if group.get("id")]
            except Exception:  # pylint: disable=broad-exception-caught
                # If groups request fails (insufficient permissions),
                # extract from access token claims as fallback
                if token_claims:
                    # wids = Windows Identity Directory Service role template IDs
                    # groups can also be in the token if configured
                    groups = token_claims.get("groups", []) or token_claims.get("wids", [])

            user_info["groups"] = groups
            return cast(dict[str, Any], user_info)

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
