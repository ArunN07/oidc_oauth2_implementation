"""GitHub OAuth2 authentication service (NOT OIDC - no id_token support)."""

import secrets
from typing import Any

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.http_client import get_http_client
from src.core.auth.oidc_client import GenericOIDCClient
from src.core.settings.app import get_settings


class GitHubAuthService(BaseAuthProvider):
    """GitHub OAuth2 service. Note: GitHub does NOT support OIDC."""

    def __init__(self):
        """Initialize GitHub OAuth2 client."""
        self.settings = get_settings()

        self.proxy = None
        if not self.settings.disable_proxy:
            self.proxy = self.settings.https_proxy or self.settings.http_proxy

        self._client = GenericOIDCClient(
            client_id=self.settings.github_client_id,
            client_secret=self.settings.github_client_secret,
            redirect_uri=self.settings.github_redirect_uri,
            token_endpoint=self.settings.github_token_url,
            authorization_endpoint=self.settings.github_authorization_url,
            scope=self.settings.github_scopes,
            user_info_endpoint=self.settings.github_user_api_url,
            use_pkce=True,
            proxy=self.proxy,
        )

    @property
    def provider_name(self) -> str:
        return "github"

    @property
    def client(self) -> GenericOIDCClient:
        return self._client

    def get_authorization_url(self, state: str | None = None) -> str:
        """Build GitHub authorization URL."""
        state = state or secrets.token_hex(16)
        auth_url, _ = self._client.build_login_redirect_url(state=state)
        return auth_url

    async def exchange_code_for_token(
        self, code: str, state: str | None = None
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        return await self._client.exchange_code_for_token(code, state=state)

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get GitHub user profile."""
        return await self._client.get_user_info(access_token)

    async def get_user_emails(self, access_token: str) -> list[dict[str, Any]]:
        """Get GitHub user emails."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with get_http_client(proxy=self.proxy) as client:
            response = await client.get("https://api.github.com/user/emails", headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_user_organizations(self, access_token: str) -> list[str]:
        """Get GitHub user organizations."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with get_http_client(proxy=self.proxy) as client:
            response = await client.get("https://api.github.com/user/orgs", headers=headers)
            response.raise_for_status()
            return [org.get("login", "") for org in response.json()]

    async def get_user_with_orgs(self, access_token: str) -> dict[str, Any]:
        """Get user info with organizations for role assignment."""
        user = await self.get_user_info(access_token)
        try:
            user["organizations"] = await self.get_user_organizations(access_token)
        except Exception:
            user["organizations"] = []
        return user


register_provider("github", GitHubAuthService)
