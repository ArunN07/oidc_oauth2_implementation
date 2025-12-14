"""
Generic OIDC Client for Authorization Code Flow.

This module provides a reusable OIDC client that is provider-agnostic
and does not depend on application-specific settings. All configuration
is passed via constructor parameters for maximum flexibility.
"""

import base64
import hashlib
import secrets
from typing import Callable
from urllib.parse import urlencode

import httpx

from src.core.auth.pkce_store import get_pkce_store


def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge pair.

    Returns
    -------
    tuple[str, str]
        A tuple of (code_verifier, code_challenge).

    Examples
    --------
    >>> verifier, challenge = generate_pkce_pair()
    >>> len(verifier) > 43
    True
    """
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def create_http_client(proxy: str | None = None, timeout: float = 30.0) -> httpx.AsyncClient:
    """
    Create an httpx async client with optional proxy.

    Parameters
    ----------
    proxy : str, optional
        Proxy URL (e.g., 'http://proxy:8080').
    timeout : float, optional
        Request timeout in seconds (default: 30.0).

    Returns
    -------
    httpx.AsyncClient
        Configured async HTTP client.

    Examples
    --------
    >>> async with create_http_client(proxy="http://proxy:8080") as client:
    ...     response = await client.get("https://api.example.com")
    """
    return httpx.AsyncClient(proxy=proxy, timeout=timeout)


class GenericOIDCClient:
    """
    A reusable OIDC client for Authorization Code Flow.

    This class is provider-agnostic and can be used with any OIDC-compliant
    identity provider. All configuration is passed via constructor.

    Parameters
    ----------
    client_id : str
        The OAuth2 client ID.
    client_secret : str
        The OAuth2 client secret.
    redirect_uri : str
        The callback URL for the authorization code.
    token_endpoint : str
        The provider's token endpoint URL.
    authorization_endpoint : str
        The provider's authorization endpoint URL.
    scope : str, optional
        Space-separated OAuth2 scopes (default: "openid profile email").
    user_info_endpoint : str, optional
        The provider's user info endpoint URL.
    use_pkce : bool, optional
        Whether to use PKCE (default: True).
    proxy : str, optional
        Proxy URL for HTTP requests.

    Examples
    --------
    >>> client = GenericOIDCClient(
    ...     client_id="my-client-id",
    ...     client_secret="my-secret",
    ...     redirect_uri="http://localhost:8000/callback",
    ...     token_endpoint="https://provider.com/oauth/token",
    ...     authorization_endpoint="https://provider.com/oauth/authorize",
    ...     proxy="http://proxy:8080",
    ... )
    >>> auth_url, state = client.build_login_redirect_url()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_endpoint: str,
        authorization_endpoint: str,
        scope: str = "openid profile email",
        user_info_endpoint: str | None = None,
        use_pkce: bool = True,
        proxy: str | None = None,
    ):
        """Initialize the OIDC client with provider configuration."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_endpoint = token_endpoint
        self.authorization_endpoint = authorization_endpoint
        self.scope = scope
        self.user_info_endpoint = user_info_endpoint
        self.use_pkce = use_pkce
        self.proxy = proxy

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client with configured proxy."""
        return create_http_client(proxy=self.proxy)

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict:
        """
        Exchange authorization code for tokens.

        Parameters
        ----------
        code : str
            The authorization code from the provider.
        state : str, optional
            The state parameter to retrieve PKCE code_verifier.

        Returns
        -------
        dict
            Token response containing access_token, id_token, refresh_token, etc.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
        }

        if self.use_pkce and state:
            code_verifier = get_pkce_store().retrieve(state)
            if code_verifier:
                data["code_verifier"] = code_verifier

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        async with self._get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    async def password_grant_login(self, username: str, password: str) -> dict:
        """
        Login using Resource Owner Password Credentials (ROPC) grant.

        Parameters
        ----------
        username : str
            The user's login name or email.
        password : str
            The user's password.

        Returns
        -------
        dict
            Token response from the provider.
        """
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
            "scope": self.scope,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with self._get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def build_login_redirect_url(
        self,
        state: str | None = None,
        prompt: str | None = None,
        extra_params: dict | None = None,
    ) -> tuple[str, str]:
        """
        Build the authorization redirect URL.

        Parameters
        ----------
        state : str, optional
            A secure random string for CSRF protection.
        prompt : str, optional
            OAuth2 prompt parameter (e.g., 'consent').
        extra_params : dict, optional
            Additional provider-specific parameters (e.g., access_type, audience).

        Returns
        -------
        tuple[str, str]
            A tuple of (authorization_url, state).

        Examples
        --------
        >>> # Basic usage
        >>> url, state = client.build_login_redirect_url()

        >>> # With Google's offline access
        >>> url, state = client.build_login_redirect_url(
        ...     prompt="consent",
        ...     extra_params={"access_type": "offline"}
        ... )

        >>> # With Auth0's audience
        >>> url, state = client.build_login_redirect_url(
        ...     extra_params={"audience": "https://my-api"}
        ... )
        """
        state = state or secrets.token_hex(16)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": self.scope,
            "state": state,
        }

        if prompt:
            params["prompt"] = prompt

        # Add any extra provider-specific parameters
        if extra_params:
            params.update(extra_params)

        if self.use_pkce:
            code_verifier, code_challenge = generate_pkce_pair()
            get_pkce_store().store(state, code_verifier)
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{self.authorization_endpoint}?{urlencode(params)}", state

    async def get_user_info(self, access_token: str) -> dict:
        """
        Fetch user information from the user info endpoint.

        Parameters
        ----------
        access_token : str
            The access token.

        Returns
        -------
        dict
            User information from the provider.

        Raises
        ------
        ValueError
            If user_info_endpoint is not configured.
        """
        if not self.user_info_endpoint:
            raise ValueError("User info endpoint not configured")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with self._get_http_client() as client:
            response = await client.get(self.user_info_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh an access token.

        Parameters
        ----------
        refresh_token : str
            The refresh token.

        Returns
        -------
        dict
            New token response.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with self._get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()
