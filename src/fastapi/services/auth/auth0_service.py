"""
Auth0 OAuth2/OIDC authentication service.

Auth0 is a flexible identity platform that supports both OAuth2 and OIDC.
It provides access_token, id_token, and refresh_token.

Attributes
----------
AUTH0_DOMAIN : str
    Your Auth0 tenant domain (e.g., dev-xxx.us.auth0.com).
AUTH0_CLIENT_ID : str
    Application client ID from Auth0 dashboard.
AUTH0_CLIENT_SECRET : str
    Application client secret from Auth0 dashboard.
"""

import secrets
from typing import Any

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.oidc_client import GenericOIDCClient
from src.core.auth.oidc_token_validator import OIDCTokenValidator
from src.core.settings.app import get_settings


class Auth0AuthService(BaseAuthProvider):
    """
    Auth0 OIDC authentication service.

    Supports both OAuth2 and OIDC flows with PKCE.
    Returns access_token, id_token, and refresh_token.
    """

    def __init__(self):
        """Initialize Auth0 OIDC client and token validator."""
        self.settings = get_settings()

        self.proxy = None
        if not self.settings.disable_proxy:
            self.proxy = self.settings.https_proxy or self.settings.http_proxy

        # Ensure offline_access is in scopes for refresh_token
        scopes = self.settings.auth0_scopes
        if "offline_access" not in scopes:
            scopes = f"{scopes} offline_access"

        self._client = GenericOIDCClient(
            client_id=self.settings.auth0_client_id,
            client_secret=self.settings.auth0_client_secret,
            redirect_uri=self.settings.auth0_redirect_uri,
            token_endpoint=self.settings.auth0_token_url,
            authorization_endpoint=self.settings.auth0_authorization_url,
            scope=scopes,
            user_info_endpoint=self.settings.auth0_user_info_url,
            use_pkce=True,
            proxy=self.proxy,
        )

        self._validator = OIDCTokenValidator(
            issuer=self.settings.auth0_issuer,
            audience=self.settings.auth0_client_id,
            jwks_uri=self.settings.auth0_jwks_uri,
            proxy=self.proxy,
        )

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "auth0"

    @property
    def client(self) -> GenericOIDCClient:
        """Return OIDC client."""
        return self._client

    @property
    def validator(self) -> OIDCTokenValidator:
        """Return token validator."""
        return self._validator

    def get_authorization_url(self, state: str | None = None) -> str:
        """
        Build authorization URL with PKCE for refresh_token support.

        Parameters
        ----------
        state : str, optional
            CSRF state parameter.

        Returns
        -------
        str
            Authorization URL to redirect user to.
        """
        state = state or secrets.token_hex(16)

        # Build extra params for Auth0
        extra_params = {}
        if self.settings.auth0_audience:
            extra_params["audience"] = self.settings.auth0_audience

        # Use GenericOIDCClient with extra_params for Auth0-specific options
        auth_url, _ = self._client.build_login_redirect_url(
            state=state,
            extra_params=extra_params if extra_params else None,
        )
        return auth_url

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Parameters
        ----------
        code : str
            Authorization code from callback.
        state : str, optional
            State parameter for PKCE retrieval.

        Returns
        -------
        dict
            Token response with access_token, id_token, refresh_token.
        """
        return await self._client.exchange_code_for_token(code, state=state)

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Validate id_token using JWKS.

        Parameters
        ----------
        id_token : str
            The id_token JWT to validate.

        Returns
        -------
        dict
            Validated token claims.
        """
        return await self._validator.validate_token(id_token)

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Get user info from Auth0 userinfo endpoint.

        Parameters
        ----------
        access_token : str
            Valid access token.

        Returns
        -------
        dict
            User information.
        """
        return await self._client.get_user_info(access_token)

    async def get_user_from_token(self, token_response: dict[str, Any]) -> dict[str, Any]:
        """
        Extract user info from id_token claims.

        Parameters
        ----------
        token_response : dict
            Token response containing id_token.

        Returns
        -------
        dict
            User information from id_token claims.
        """
        id_token = token_response.get("id_token")
        if id_token:
            claims = self.decode_id_token(id_token)
            return {
                "sub": claims.get("sub"),
                "name": claims.get("name"),
                "email": claims.get("email"),
                "picture": claims.get("picture"),
                "email_verified": claims.get("email_verified"),
                "nickname": claims.get("nickname"),
            }

        # Fallback to userinfo endpoint
        access_token = token_response.get("access_token")
        if access_token:
            return await self.get_user_info(access_token)

        return {}

    def decode_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Decode id_token without validation (for extracting claims).

        Parameters
        ----------
        id_token : str
            The id_token JWT.

        Returns
        -------
        dict
            Token claims.
        """
        import base64
        import json

        parts = id_token.split(".")
        if len(parts) != 3:
            return {}

        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        try:
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception:
            return {}


# Register Auth0 provider
register_provider("auth0", Auth0AuthService)

