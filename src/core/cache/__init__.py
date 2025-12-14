"""
Cache module for OAuth2/OIDC state management.

This module provides in-memory caching for temporary data during
OAuth2 flows, such as PKCE code_verifiers and state tokens.

Exports
-------
cache : InMemoryCache
    Singleton cache instance ready to use.
InMemoryCache : class
    Thread-safe cache class with TTL support.

Examples
--------
>>> from src.core.cache import cache
>>> cache.set("key", "value", ttl_seconds=300)
>>> cache.get("key")
'value'
"""

from src.core.cache.memory_cache import InMemoryCache, cache

__all__ = ["cache", "InMemoryCache"]
