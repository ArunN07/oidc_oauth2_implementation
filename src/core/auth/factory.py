from src.core.auth.base import BaseAuthProvider
from src.core.exceptions.exceptions import ProviderNotSupportedError
from src.core.settings.app import get_settings

# Provider registry - populated by services when they import
_provider_registry: dict[str, type[BaseAuthProvider]] = {}


def register_provider(name: str, provider_class: type[BaseAuthProvider]) -> None:
    """
    Register an authentication provider.

    Called by each service module to register itself.

    Parameters
    ----------
    name : str
        Provider name ('github', 'azure', 'google').
    provider_class : Type[BaseAuthProvider]
        The provider class to register.
    """
    _provider_registry[name.lower()] = provider_class


def get_auth_provider(provider: str | None = None) -> BaseAuthProvider:
    """
    Get an authentication provider instance.

    Creates and returns the appropriate authentication provider based on
    the provider parameter or the AUTH_PROVIDER environment variable.

    Parameters
    ----------
    provider : str, optional
        Provider name override ('github', 'azure', 'google').
        If not provided, uses AUTH_PROVIDER from .env.

    Returns
    -------
    BaseAuthProvider
        The authentication provider instance.

    Raises
    ------
    ProviderNotSupportedError
        If the requested provider is not supported.
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
    Get a specific provider by name (always creates the specified provider).

    Parameters
    ----------
    name : str
        Provider name ('github', 'azure', 'google').

    Returns
    -------
    BaseAuthProvider
        The authentication provider instance.
    """
    return get_auth_provider(provider=name)
