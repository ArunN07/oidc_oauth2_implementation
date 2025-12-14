"""
Base authentication provider interface.

This module defines the abstract base class for OAuth2/OIDC authentication
providers. All provider implementations (GitHub, Azure, Google) must inherit
from BaseAuthProvider and implement its abstract methods.

The base class establishes a consistent interface for:
- Building authorization URLs
- Exchanging authorization codes for tokens
- Fetching user information
- Token refresh (optional)
- Token validation (optional)

Classes
-------
BaseAuthProvider
    Abstract base class defining the authentication provider interface.

Examples
--------
Implementing a custom provider:

>>> class MyProvider(BaseAuthProvider):
...     @property
...     def provider_name(self) -> str:
...         return "my_provider"
...
...     def get_authorization_url(self, state: str | None = None) -> str:
...         return f"https://auth.example.com/authorize?state={state}"
...
...     async def exchange_code_for_token(self, code: str, state: str | None = None):
...         # Exchange code for tokens
...         return {"access_token": "..."}
...
...     async def get_user_info(self, access_token: str):
...         # Fetch user info
...         return {"id": "123", "name": "User"}
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAuthProvider(ABC):
    """
    Abstract base class for OAuth2/OIDC authentication providers.

    This class defines the interface that all authentication providers must
    implement. It ensures consistent behavior across different identity
    providers (GitHub, Azure AD, Google, etc.).

    Methods
    -------
    provider_name : str
        Property returning the provider's identifier.
    get_authorization_url(state)
        Build the OAuth2/OIDC authorization URL.
    exchange_code_for_token(code, state)
        Exchange authorization code for access token(s).
    get_user_info(access_token)
        Fetch user information using the access token.
    refresh_token(refresh_token)
        Refresh the access token (optional, raises NotImplementedError by default).
    validate_token(token)
        Validate a token (optional, raises NotImplementedError by default).

    Notes
    -----
    - OAuth2-only providers (like GitHub) don't need to implement refresh_token
      or validate_token.
    - OIDC providers should implement all methods for full functionality.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the provider name.

        Returns
        -------
        str
            Provider identifier (e.g., 'github', 'azure', 'google').
        """
        pass

    @abstractmethod
    def get_authorization_url(self, state: str | None = None) -> str:
        """
        Build the authorization URL for OAuth2/OIDC flow.

        Parameters
        ----------
        state : str | None, optional
            State parameter for CSRF protection. If not provided,
            implementations should generate a random state.

        Returns
        -------
        str
            Complete authorization URL to redirect the user to.
        """
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self, code: str, state: str | None = None
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token(s).

        Parameters
        ----------
        code : str
            Authorization code received from the identity provider.
        state : str | None, optional
            State parameter for PKCE verification.

        Returns
        -------
        dict[str, Any]
            Token response containing:
            - access_token: Always present
            - id_token: Present for OIDC providers
            - refresh_token: Present if supported and requested
            - expires_in: Token lifetime in seconds
            - token_type: Usually "Bearer"
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Get user information using the access token.

        Parameters
        ----------
        access_token : str
            Valid access token from the identity provider.

        Returns
        -------
        dict[str, Any]
            User information. Structure varies by provider but typically includes:
            - id/sub: Unique user identifier
            - name: Display name
            - email: Email address
        """
        pass

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh the access token using a refresh token.

        Parameters
        ----------
        refresh_token : str
            Valid refresh token.

        Returns
        -------
        dict[str, Any]
            New token response with fresh access_token.

        Raises
        ------
        NotImplementedError
            If the provider doesn't support token refresh.

        Notes
        -----
        GitHub doesn't support token refresh. Azure and Google do.
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support token refresh"
        )

    async def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate a token and return its payload.

        Parameters
        ----------
        token : str
            Token to validate (usually id_token).

        Returns
        -------
        dict[str, Any]
            Decoded and validated token claims.

        Raises
        ------
        NotImplementedError
            If the provider doesn't support token validation.

        Notes
        -----
        OAuth2-only providers (GitHub) can't validate tokens locally.
        OIDC providers validate JWTs using JWKS endpoints.
        """
        raise NotImplementedError(
            f"{self.provider_name} does not support token validation"
        )
