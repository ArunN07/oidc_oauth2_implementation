from collections.abc import Callable
from logging import Logger

from fastapi import Depends
from fastapi.params import Depends as DependsType

from delphi_studio_backend.core.cache.base_cache import BaseCache
from delphi_studio_backend.core.cache.cache_types import CacheType
from delphi_studio_backend.core.cache.in_memory_cache import InMemoryCache
from delphi_studio_backend.core.cache.redis_cache import RedisCache
from delphi_studio_backend.core.configuration.logger_dependency import get_logger
from delphi_studio_backend.core.settings.app import app_settings

# Cache singleton registry
_cached_instances: dict[CacheType | None, BaseCache] = {}

# Mapping of concrete cache classes to their enum identifiers
CACHE_BACKEND_REGISTRY: dict[type[BaseCache], CacheType] = {
    InMemoryCache: CacheType.MEMORY,
    RedisCache: CacheType.REDIS,
}


def get_cache_dependency(cache_type: CacheType | None = None) -> Callable[..., BaseCache]:
    """
    Factory returning a FastAPI-compatible dependency function for cache instances.

    This function can be used in two contexts:
    1. Inside FastAPI endpoints:
        >>> cache: BaseCache = Depends(get_cache_dependency())

    2. In regular Python code or services:
        >>> cache = get_cache_dependency(CacheType.REDIS)()

    Parameters
    ----------
    cache_type : CacheType | None, optional
        The desired cache backend. If None, the backend will be selected
        based on `app_settings.use_in_memory_cache`.

    Returns
    -------
    Callable[..., BaseCache]
        Dependency function that provides a concrete cache instance.

    Notes
    -----
    - In FastAPI routes, **always** use `Depends(get_cache_dependency())`
      (parentheses required).
    - When used manually, remember to call the inner function `()`.
    """

    def dependency(logger: Logger = Depends(get_logger)) -> BaseCache:
        """
        Inner dependency executed by FastAPI or called directly.

        Parameters
        ----------
        logger : Logger
            Logger instance injected by FastAPI or resolved manually.

        Returns
        -------
        BaseCache
            The resolved cache instance (RedisCache or InMemoryCache).
        """
        # Handle manual invocation: FastAPI's Depends placeholder may be passed
        if isinstance(logger, DependsType):
            logger = get_logger()

        # Reuse cached instance if already initialized
        if cache_type in _cached_instances:
            return _cached_instances[cache_type]

        # Create the appropriate cache backend
        cache: BaseCache
        if cache_type == CacheType.MEMORY:
            cache = InMemoryCache()
        elif cache_type == CacheType.REDIS:
            cache = RedisCache(redis_url=app_settings.redis_url)
        else:
            cache = (
                InMemoryCache() if app_settings.use_in_memory_cache else RedisCache(redis_url=app_settings.redis_url)
            )

        # Store and log the resolved backend
        _cached_instances[cache_type] = cache
        resolved_type = CACHE_BACKEND_REGISTRY.get(type(cache), CacheType.MEMORY)
        logger.info(
            f"[CacheFactory] Using {resolved_type.value.upper()} cache "
            f"({cache.__class__.__name__}) - "
            f"{'explicit' if cache_type else 'from app_settings'} selection"
        )

        return cache

    return dependency
