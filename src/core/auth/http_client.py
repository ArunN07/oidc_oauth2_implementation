"""
HTTP client utilities with proxy support.

This module provides HTTP client factory functions that respect
application proxy settings. It's separate from the generic OIDC client
to maintain loose coupling.
"""

import httpx

from src.core.settings.app import get_settings


def get_http_client(proxy: str | None = None) -> httpx.AsyncClient:
    """
    Get httpx async client with proxy settings.

    Parameters
    ----------
    proxy : str, optional
        Explicit proxy URL. If None, uses settings-based proxy.

    Returns
    -------
    httpx.AsyncClient
        Async HTTP client configured with proxy if enabled.

    Examples
    --------
    >>> async with get_http_client() as client:
    ...     response = await client.get("https://api.example.com")
    """
    if proxy is None:
        settings = get_settings()
        if not settings.disable_proxy:
            proxy = settings.https_proxy or settings.http_proxy

    return httpx.AsyncClient(proxy=proxy, timeout=30.0)


def get_proxy_url() -> str | None:
    """
    Get configured proxy URL from settings.

    Returns
    -------
    str | None
        Proxy URL if configured and not disabled, None otherwise.
    """
    settings = get_settings()
    if settings.disable_proxy:
        return None
    return settings.https_proxy or settings.http_proxy

