"""
In-memory cache implementation for OAuth2/OIDC state management.

This module provides a thread-safe, singleton in-memory cache with TTL
(Time-To-Live) support. It's used for storing temporary data during
OAuth2 flows, such as PKCE code_verifiers and state tokens.

Why Cache is Used:
-----------------
OAuth2/OIDC flows require storing temporary state between requests:
1. **PKCE code_verifier**: Stored during authorization, retrieved at callback
2. **State tokens**: For CSRF protection and request correlation
3. **Nonces**: For id_token replay prevention (OIDC)

Cache Features:
--------------
- **Singleton Pattern**: Single instance shared across the application
- **Thread-Safe**: Uses locks for concurrent access
- **TTL Support**: Automatic expiration of entries
- **Cleanup**: Expired entries removed on access

For Production:
--------------
This in-memory cache is suitable for:
- Development and testing
- Single-process deployments
- Small-scale applications

For multi-process or distributed deployments, use Redis cache instead.

Classes
-------
InMemoryCache
    Thread-safe singleton cache with TTL support.

Examples
--------
Using the cache singleton:

>>> from src.core.cache.memory_cache import cache
>>>
>>> # Store with 5-minute TTL
>>> cache.set("my_key", "my_value", ttl_seconds=300)
>>>
>>> # Retrieve
>>> value = cache.get("my_key")
>>>
>>> # Pop (get and delete)
>>> value = cache.pop("my_key")
"""

import time
from threading import Lock


class InMemoryCache:
    """
    Thread-safe singleton in-memory cache with TTL support.

    This cache implements the Singleton pattern to ensure a single shared
    instance across the application. All operations are thread-safe.

    Attributes
    ----------
    _instance : InMemoryCache | None
        Class-level singleton instance.
    _lock : Lock
        Class-level lock for singleton creation.
    _store : dict
        Internal storage: {key: (value, expires_at)}
    _store_lock : Lock
        Instance-level lock for thread-safe operations.

    Methods
    -------
    set(key, value, ttl_seconds)
        Store a value with TTL.
    get(key)
        Get a value by key.
    pop(key)
        Get and remove a value.
    delete(key)
        Delete a key.
    clear()
        Clear all entries.

    Examples
    --------
    >>> cache = InMemoryCache()
    >>> cache.set("state:abc123", "verifier_xyz", ttl_seconds=600)
    >>> cache.get("state:abc123")
    'verifier_xyz'
    """

    _instance: "InMemoryCache | None" = None
    _lock = Lock()
    _store: dict[str, tuple[str, float]]
    _store_lock: Lock

    def __new__(cls) -> "InMemoryCache":
        """
        Create or return the singleton instance.

        Returns
        -------
        InMemoryCache
            The singleton cache instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._store = {}
                    cls._instance._store_lock = Lock()
        return cls._instance

    def set(self, key: str, value: str, ttl_seconds: int = 600) -> None:
        """
        Store a value with TTL.

        Parameters
        ----------
        key : str
            Cache key.
        value : str
            Value to store.
        ttl_seconds : int, optional
            Time-to-live in seconds (default: 600 = 10 minutes).

        Notes
        -----
        Expired entries are cleaned up before adding new entries.
        """
        with self._store_lock:
            self._cleanup_expired()
            expires_at = time.time() + ttl_seconds
            self._store[key] = (value, expires_at)

    def get(self, key: str) -> str | None:
        """
        Get a value by key.

        Parameters
        ----------
        key : str
            Cache key to retrieve.

        Returns
        -------
        str | None
            The cached value, or None if not found or expired.
        """
        with self._store_lock:
            self._cleanup_expired()
            if key in self._store:
                value, expires_at = self._store[key]
                if time.time() < expires_at:
                    return str(value)
                del self._store[key]
            return None

    def pop(self, key: str) -> str | None:
        """
        Get and remove a value by key.

        This is the preferred method for one-time-use values like
        PKCE code_verifiers.

        Parameters
        ----------
        key : str
            Cache key to retrieve and remove.

        Returns
        -------
        str | None
            The cached value, or None if not found or expired.
        """
        with self._store_lock:
            self._cleanup_expired()
            if key in self._store:
                value, expires_at = self._store.pop(key)
                if time.time() < expires_at:
                    return str(value)
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Parameters
        ----------
        key : str
            Cache key to delete.

        Returns
        -------
        bool
            True if the key existed and was deleted, False otherwise.
        """
        with self._store_lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._store_lock:
            self._store.clear()

    def _cleanup_expired(self) -> None:
        """
        Remove expired entries from the cache.

        Called internally before set/get/pop operations.
        """
        current_time = time.time()
        expired_keys = [key for key, (_, expires_at) in self._store.items() if current_time >= expires_at]
        for key in expired_keys:
            del self._store[key]


# Singleton instance - use this in your code
cache = InMemoryCache()
