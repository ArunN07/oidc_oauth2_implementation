"""
GitHub OAuth2 Authentication Service.

This module provides GitHub OAuth2 authentication support. Note that GitHub
does NOT support OIDC, so no id_token is returned.
"""

import secrets
from typing import Any, cast

import httpx

from src.core.auth.base import BaseAuthProvider
from src.core.auth.factory import register_provider
from src.core.auth.http_client import get_http_client
from src.core.auth.oidc_client import GenericOIDCClient
from src.core.settings.app import get_settings


class GitHubAuthService(BaseAuthProvider):
    """GitHub OAuth2 service. Note: GitHub does NOT support OIDC."""

    def __init__(self) -> None:
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
        """Return provider identifier."""
        return "github"

    @property
    def client(self) -> GenericOIDCClient:
        """Return the OIDC client instance."""
        return cast(GenericOIDCClient, self._client)

    def get_authorization_url(self, state: str | None = None) -> str:
        """Build GitHub authorization URL."""
        state = state or secrets.token_hex(16)
        auth_url, _ = self._client.build_login_redirect_url(state=state)
        return cast(str, auth_url)

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        return cast(dict[str, Any], await self._client.exchange_code_for_token(code, state=state))

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get GitHub user profile."""
        return cast(dict[str, Any], await self._client.get_user_info(access_token))

    async def get_user_emails(self, access_token: str) -> list[dict[str, Any]]:
        """Get GitHub user emails."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with get_http_client(proxy=self.proxy) as client:
            response = await client.get("https://api.github.com/user/emails", headers=headers)
            response.raise_for_status()
            return cast(list[dict[str, Any]], response.json())

    async def get_user_organizations(self, access_token: str) -> list[str]:
        """Get GitHub user organizations."""
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        async with get_http_client(proxy=self.proxy) as client:
            response = await client.get("https://api.github.com/user/orgs", headers=headers)
            response.raise_for_status()
            return [org.get("login", "") for org in response.json()]

    async def get_user_teams(self, access_token: str) -> list[str]:
        """
        Get GitHub user's team memberships across all organizations.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            List of team slugs the user is a member of

        Note: Requires 'read:org' scope to access team information.
        """
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        teams = []

        async with get_http_client(proxy=self.proxy) as client:
            try:
                # Use the /user/teams endpoint which returns only teams the user is a member of
                teams_url = "https://api.github.com/user/teams"
                teams_response = await client.get(
                    teams_url, headers=headers, params={"per_page": 100}  # Get up to 100 teams
                )

                if teams_response.status_code == 200:
                    user_teams = teams_response.json()
                    # Extract team slugs (only teams user is actually a member of)
                    for team in user_teams:
                        team_slug = team.get("slug", "")
                        if team_slug and team_slug not in teams:
                            teams.append(team_slug)

            except httpx.HTTPError:
                # If /user/teams doesn't work, return empty list
                pass

        return teams

    async def get_user_with_orgs(self, access_token: str) -> dict[str, Any]:
        """Get user info with organizations, teams, and email for role assignment."""
        user = await self.get_user_info(access_token)

        # Fetch organizations
        organizations = []
        try:
            organizations = await self.get_user_organizations(access_token)
            user["organizations"] = organizations
        except httpx.HTTPError:
            user["organizations"] = []

        # Fetch teams (for custom role detection)
        try:
            user["teams"] = await self.get_user_teams(access_token)
        except httpx.HTTPError:
            user["teams"] = []

        if not user.get("email"):
            try:
                emails = await self.get_user_emails(access_token)
                # Find the primary verified email
                primary_email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
                if primary_email:
                    user["email"] = primary_email
                # If no primary email, use the first verified email
                elif emails:
                    verified_email = next((e["email"] for e in emails if e.get("verified")), None)
                    if verified_email:
                        user["email"] = verified_email
            except httpx.HTTPError:
                # If we can't fetch emails, leave it as None
                pass

        return user


register_provider("github", GitHubAuthService)
