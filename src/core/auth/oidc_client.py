import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

from src.core.auth.pkce_store import get_pkce_store
from src.core.settings.app import get_settings


def _generate_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge pair.

    Returns
    -------
    Tuple[str, str]
        A tuple of (code_verifier, code_challenge).
    """
    # Generate a random code_verifier (43-128 characters)
    code_verifier = secrets.token_urlsafe(64)

    # Create code_challenge = BASE64URL(SHA256(code_verifier))
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")

    return code_verifier, code_challenge


def _get_http_client() -> httpx.AsyncClient:
    """Get httpx client with proxy settings from settings."""
    settings = get_settings()
    proxy = None

    if not settings.disable_proxy:
        proxy = settings.https_proxy or settings.http_proxy

    return httpx.AsyncClient(proxy=proxy, timeout=30.0)


class GenericOIDCClient:
    """
    A reusable OIDC client for Authorization Code Flow.

    This class encapsulates token exchange logic and login URL generation
    for OpenID Connect-compatible identity providers.

    Attributes
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
    scope : str
        Space-separated OAuth2 scopes.
    user_info_endpoint : str, optional
        The provider's user info endpoint URL.

    Methods
    -------
    build_login_redirect_url(state=None)
        Generate the authorization URL.
    exchange_code_for_token(code)
        Exchange authorization code for tokens.
    get_user_info(access_token)
        Fetch user information.
    refresh_token(refresh_token)
        Refresh the access token.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_endpoint: str,
        authorization_endpoint: str,
        scope: str = "openid profile email",
        user_info_endpoint: Optional[str] = None,
        use_pkce: bool = True,
    ):
        """
        Initialize the OIDC client.

        Parameters
        ----------
        client_id : str
            The client ID registered with the identity provider.
        client_secret : str
            The client secret associated with the client ID.
        redirect_uri : str
            The redirect URI used in the Authorization Code Flow.
        token_endpoint : str
            The URL for exchanging authorization codes or credentials for tokens.
        authorization_endpoint : str
            The URL to initiate the Authorization Code Flow.
        scope : str, optional
            Space-separated scopes to request (default is "openid profile email").
        user_info_endpoint : str, optional
            The URL to fetch user information.
        use_pkce : bool, optional
            Whether to use PKCE for enhanced security (default is True).
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_endpoint = token_endpoint
        self.authorization_endpoint = authorization_endpoint
        self.scope = scope
        self.user_info_endpoint = user_info_endpoint
        self.use_pkce = use_pkce
        # PKCE verifiers are stored in global PKCEStore for persistence across requests

    async def exchange_code_for_token(self, code: str, state: str | None = None) -> dict:
        """
        Exchanges an authorization code for access and ID tokens.

        Parameters
        ----------
        code : str
            The authorization code received from the identity provider after login.
        state : str, optional
            The state parameter to retrieve the PKCE code_verifier.

        Returns
        -------
        dict
            A dictionary containing `access_token`, `refresh_token`, `id_token`, etc.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,  # Include scope for Azure to return refresh_token
        }

        # Add PKCE code_verifier if available from global store
        if self.use_pkce and state:
            code_verifier = get_pkce_store().retrieve(state)
            if code_verifier:
                data["code_verifier"] = code_verifier

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        async with _get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    async def password_grant_login(self, username: str, password: str) -> dict:
        """
        Logs in using the Resource Owner Password Credentials (ROPC) grant.

        Parameters
        ----------
        username : str
            The user's login name or email.
        password : str
            The user's password.

        Returns
        -------
        dict
            A dictionary containing tokens from the identity provider.
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
        async with _get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def build_login_redirect_url(
        self, state: str | None = None, prompt: str | None = None
    ) -> tuple[str, str]:
        """
        Constructs the login redirect URL for Authorization Code Flow with PKCE.

        Parameters
        ----------
        state : str, optional
            A secure random string used to maintain request and callback state.
        prompt : str, optional
            OAuth2 prompt parameter (e.g., 'consent' to force consent and get refresh_token).

        Returns
        -------
        Tuple[str, str]
            A tuple of (authorization_url, state).
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

        # Add prompt parameter if specified (needed for refresh_token in Azure)
        if prompt:
            params["prompt"] = prompt

        # Add PKCE parameters if enabled
        if self.use_pkce:
            code_verifier, code_challenge = _generate_pkce_pair()
            get_pkce_store().store(state, code_verifier)
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{self.authorization_endpoint}?{urlencode(params)}", state

    async def get_user_info(self, access_token: str) -> dict:
        """
        Fetches user information from the user info endpoint.

        Parameters
        ----------
        access_token : str
            The access token.

        Returns
        -------
        dict
            User information from the provider.
        """
        if not self.user_info_endpoint:
            raise ValueError("User info endpoint not configured")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with _get_http_client() as client:
            response = await client.get(self.user_info_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refreshes an access token using a refresh token.

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
        async with _get_http_client() as client:
            response = await client.post(self.token_endpoint, data=data, headers=headers)
        response.raise_for_status()
        return response.json()
