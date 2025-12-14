"""
Provider factory and registry for OAuth2/OIDC authentication.

This module implements the Factory pattern for authentication providers,
allowing dynamic provider registration and retrieval. Providers register
themselves when their modules are imported.

Why use register_provider?
--------------------------
The factory pattern with registration provides:
1. **Loose Coupling**: Core module doesn't need to import all providers
2. **Extensibility**: New providers can be added without modifying factory code
3. **Configuration-driven**: Provider selection based on environment variables
4. **Testability**: Easy to mock providers in tests

How it works:
1. Each provider service calls `register_provider()` when imported
2. The factory stores provider classes in `_provider_registry`
3. `get_auth_provider()` creates instances on demand

Functions
---------
register_provider
    Register a provider class with the factory.
get_auth_provider
    Get a provider instance (uses settings or parameter).
get_provider_by_name
    Get a specific provider by name.

Examples
--------
Registering a provider (done in service module):

>>> from src.core.auth.factory import register_provider
>>> from src.core.auth.base import BaseAuthProvider
>>>
>>> class MyProvider(BaseAuthProvider):
...     # implementation
...     pass
>>>
>>> register_provider("my_provider", MyProvider)

Getting a provider:

>>> from src.core.auth.factory import get_auth_provider
>>>
>>> # Use default from settings
>>> provider = get_auth_provider()
>>>
>>> # Or specify explicitly
>>> github = get_auth_provider("github")
"""

from src.core.auth.base import BaseAuthProvider
from src.core.exceptions.exceptions import ProviderNotSupportedError
from src.core.settings.app import get_settings

# Provider registry - populated by services when they import
_provider_registry: dict[str, type[BaseAuthProvider]] = {}


def register_provider(name: str, provider_class: type[BaseAuthProvider]) -> None:
    """
    Register an authentication provider with the factory.

    This function is called by each provider service module to register
    itself with the factory. Registration happens at import time.

    Parameters
    ----------
    name : str
        Provider name (e.g., 'github', 'azure', 'google').
        Case-insensitive (converted to lowercase).
    provider_class : type[BaseAuthProvider]
        The provider class to register. Must inherit from BaseAuthProvider.

    Examples
    --------
    In a provider service module:

    >>> class GitHubAuthService(BaseAuthProvider):
    ...     # implementation
    ...     pass
    >>>
    >>> register_provider("github", GitHubAuthService)

    Notes
    -----
    - Registration is idempotent; re-registering overwrites previous entry
    - Provider name is case-insensitive ('GitHub' == 'github')
    """
    _provider_registry[name.lower()] = provider_class


def get_auth_provider(provider: str | None = None) -> BaseAuthProvider:
    """
    Get an authentication provider instance.

    Creates and returns the appropriate authentication provider based on
    the provider parameter or the AUTH_PROVIDER environment variable.

    Parameters
    ----------
    provider : str | None, optional
        Provider name ('github', 'azure', 'google').
        If not provided, uses AUTH_PROVIDER from settings.

    Returns
    -------
    BaseAuthProvider
        A new instance of the requested provider.

    Raises
    ------
    ProviderNotSupportedError
        If the requested provider is not registered.

    Examples
    --------
    >>> # Use default provider from settings
    >>> provider = get_auth_provider()
    >>>
    >>> # Use specific provider
    >>> github = get_auth_provider("github")
    >>> azure = get_auth_provider("azure")

    Notes
    -----
    A new instance is created on each call. This is intentional to avoid
    sharing state between requests in async contexts.
    """
    settings = get_settings()

    # Determine provider - use parameter if provided, otherwise use settings
    if provider:
        provider_name = provider.lower()
    else:
        provider_name = settings.auth_provider.value

    if provider_name not in _provider_registry:
        raise ProviderNotSupportedError(provider_name)

    return _provider_registry[provider_name]()


def get_provider_by_name(name: str) -> BaseAuthProvider:
    """
    Get a specific provider by name.

    Convenience function that always creates the specified provider,
    ignoring the default from settings.

    Parameters
    ----------
    name : str
        Provider name ('github', 'azure', 'google').

    Returns
    -------
    BaseAuthProvider
        A new instance of the specified provider.

    Raises
    ------
    ProviderNotSupportedError
        If the provider is not registered.

    Examples
    --------
    >>> github = get_provider_by_name("github")
    >>> azure = get_provider_by_name("azure")
    """
    return get_auth_provider(provider=name)
