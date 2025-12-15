"""
OIDC Token Validator.

This module provides JWT token validation using OIDC standards including
JWKS-based signature verification, issuer validation, and audience checks.
"""

import time
from typing import Any, cast

import httpx
from jose import JWTError, jwt


class OIDCTokenValidator:
    """
    Validates JWT tokens using OIDC issuer, audience, and JWKS.

    This class fetches and caches JWKS keys, verifies JWTs using the correct
    key ID (kid), and validates standard OIDC claims.

    Attributes
    ----------
    issuer : str
        The expected token issuer.
    audience : str
        The expected token audience.
    jwks_uri : str
        URL to fetch the JSON Web Key Set.
    cache_ttl : int
        Time-to-live for cached JWKS in seconds.
    proxy : str, optional
        Optional proxy URL for JWKS requests.

    Methods
    -------
    validate_token(token)
        Validate and decode a JWT token.
    decode_token_unverified(token)
        Decode a token without validation.
    """

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_uri: str,
        cache_ttl: int = 3600,
        proxy: str | None = None,
    ):
        """
        Initialize the OIDC token validator.

        Parameters
        ----------
        issuer : str
            The expected issuer of the token.
        audience : str
            The expected audience (usually your backend client ID).
        jwks_uri : str
            The URL to fetch the JSON Web Key Set.
        cache_ttl : int, optional
            How long to cache the JWKS in seconds. Default is 3600 (1 hour).
        proxy : str, optional
            Optional proxy URL.
        """
        self.issuer = issuer
        self.audience = audience
        self.jwks_uri = jwks_uri
        self.cache_ttl = cache_ttl
        self.proxy = proxy

        self._jwks_cache: dict | None = None
        self._jwks_fetched_at: float = 0.0

    async def _fetch_jwks(self) -> dict[Any, Any]:
        """
        Fetch JWKS from the configured URI.

        Returns
        -------
        dict
            The JWKS JSON dictionary.
        """
        try:
            transport = httpx.AsyncHTTPTransport(proxy=self.proxy) if self.proxy else None
            async with httpx.AsyncClient(transport=transport) as client:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()
                return cast(dict[Any, Any], response.json())
        except httpx.RequestError as e:
            raise JWTError(f"Failed to fetch JWKS: {e}") from e

    async def _get_jwks(self, force_refresh: bool = False) -> dict:
        """
        Get cached JWKS or fetch new if expired or forced.

        Parameters
        ----------
        force_refresh : bool, optional
            Force re-fetch JWKS even if cache is valid.

        Returns
        -------
        dict
            The JWKS JSON dictionary.
        """
        now = time.time()
        if not force_refresh and self._jwks_cache and (now - self._jwks_fetched_at) < self.cache_ttl:
            return self._jwks_cache

        self._jwks_cache = await self._fetch_jwks()
        self._jwks_fetched_at = now
        return self._jwks_cache

    async def _get_key(self, kid: str) -> dict[Any, Any]:
        """
        Get a public key from JWKS by `kid`, with automatic refresh if not found.

        Parameters
        ----------
        kid : str
            The Key ID from JWT header.

        Returns
        -------
        dict
            The public key matching the `kid`.
        """
        jwks = await self._get_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)

        if not key:
            jwks = await self._get_jwks(force_refresh=True)
            key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)

        if not key:
            raise JWTError(f"Public key with kid '{kid}' not found.")

        return cast(dict[Any, Any], key)

    async def validate_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT token using JWKS and OIDC settings.

        Parameters
        ----------
        token : str
            The raw JWT token string.

        Returns
        -------
        dict
            The validated payload of the token.
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            if not kid:
                raise JWTError("Missing 'kid' in token header.")

            key = await self._get_key(kid)

            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
            return cast(dict[str, Any], payload)
        except JWTError as e:
            raise JWTError(f"Token validation failed: {e}") from e

    def decode_token_unverified(self, token: str) -> dict[str, Any]:
        """
        Decode a JWT token without verification (for extracting claims only).

        Parameters
        ----------
        token : str
            The raw JWT token string.

        Returns
        -------
        dict
            The token payload.
        """
        return cast(dict[str, Any], jwt.get_unverified_claims(token))
