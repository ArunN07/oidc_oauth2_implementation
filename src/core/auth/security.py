"""
Security schemes for OAuth2/OIDC authentication.

This module provides centralized security scheme configurations for FastAPI.
All authentication-related security dependencies should be defined here.

Attributes
----------
bearer_scheme : HTTPBearer
    Bearer token security scheme for protected endpoints.

Examples
--------
Using the bearer scheme in a protected endpoint:

>>> from fastapi import Depends
>>> from src.core.auth.security import bearer_scheme
>>>
>>> @router.get("/protected")
>>> async def protected_endpoint(
...     credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
... ):
...     token = credentials.credentials
...     return {"token": token}
"""

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=True, scheme_name="BearerAuth")


def get_bearer_token(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Extract the bearer token from credentials.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials
        Credentials from HTTPBearer dependency.

    Returns
    -------
    str
        The bearer token string.

    Examples
    --------
    >>> @router.get("/protected")
    >>> async def endpoint(credentials = Depends(bearer_scheme)):
    ...     token = get_bearer_token(credentials)
    ...     return {"token": token}
    """
    return credentials.credentials
