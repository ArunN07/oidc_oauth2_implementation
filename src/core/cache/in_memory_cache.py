from __future__ import annotations

import fnmatch
import time
from threading import Lock
from typing import Any

from delphi_studio_backend.core.cache.base_cache import BaseCache


class InMemoryCache(BaseCache):
    """
    Thread-safe singleton in-memory cache with optional per-key TTL.

    This cache maintains key–value pairs locally with optional expiration
    and supports wildcard-based key matching similar to Redis.

    Notes
    -----
    - Implements the Singleton pattern so the same cache instance is reused
      across the process. This avoids data loss when multiple FastAPI requests
      share the same in-memory store.
    - Thread-safe through use of :class:`threading.Lock`.
    - Best suited for local development or single-process deployments.
    """

    _instance: InMemoryCache | None = None

    def __new__(cls: type[InMemoryCache], *args: Any, **kwargs: Any) -> InMemoryCache:
        """Ensure a single shared instance across all calls."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, maxsize: int = 10_000):
        """
        Initialize the in-memory cache.

        Parameters
        ----------
        maxsize : int, default=10_000
            Maximum number of items to store in the cache.
        """
        if getattr(self, "_initialized", False):
            return
        self.cache: dict[str, tuple[str, float | None]] = {}
        self.maxsize = maxsize
        self.lock = Lock()
        self._initialized = True

    def get(self, key: str) -> str | None:
        """
        Retrieve a cached value by key.

        Parameters
        ----------
        key : str
            The cache key to retrieve.

        Returns
        -------
        str | None
            The cached value if present and not expired, otherwise ``None``.
        """
        with self.lock:
            if key not in self.cache:
                return None

            value, expiry_time = self.cache[key]

            if expiry_time is not None and time.time() > expiry_time:
                del self.cache[key]
                return None

            return value

    def set(self, key: str, value: str, expire: int | None = None) -> None:
        """
        Store a key–value pair in the cache.

        Parameters
        ----------
        key : str
            Cache key.
        value : str
            Value to store.
        expire : int | None, optional
            TTL in seconds. If ``None``, key never expires.
        """
        with self.lock:
            expiry_time = None if expire is None else time.time() + expire
            self.cache[key] = (value, expiry_time)

            if len(self.cache) > self.maxsize:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

    def delete(self, key: str) -> int:
        """
        Delete a key from the cache.

        Parameters
        ----------
        key : str
            Key to remove.

        Returns
        -------
        int
            ``1`` if the key existed and was deleted, otherwise ``0``.
        """
        with self.lock:
            existed = key in self.cache
            self.cache.pop(key, None)
            return 1 if existed else 0

    def clear_all(self, pattern: str | None = None) -> int:
        """
        Clear cache entries that match a wildcard pattern.

        Parameters
        ----------
        pattern : str | None, optional
            Wildcard pattern (e.g., ``"metrics_*"`` or ``"*_cache"``).
            If ``None`` or ``"*"`` is provided, all keys are cleared.

        Returns
        -------
        int
            Number of deleted entries.
        """
        with self.lock:
            if not pattern or pattern == "*":
                count = len(self.cache)
                self.cache.clear()
                return count

            keys_to_remove = [k for k in self.cache if fnmatch.fnmatch(k, pattern)]
            for k in keys_to_remove:
                self.cache.pop(k, None)
            return len(keys_to_remove)

    def list_keys(self, pattern: str | None = None) -> list[str]:
        """
        List keys currently stored in the cache.

        Parameters
        ----------
        pattern : str | None, optional
            Wildcard pattern (e.g., ``"metrics_*"``) for filtering keys.
            If ``None`` or ``"*"`` is given, returns all keys.

        Returns
        -------
        list[str]
            List of matching keys.
        """
        with self.lock:
            keys = list(self.cache.keys())
            if not pattern or pattern == "*":
                return keys
            return [k for k in keys if fnmatch.fnmatch(k, pattern)]
