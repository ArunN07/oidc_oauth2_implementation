"""In-memory cache implementation."""

import time
from threading import Lock


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""

    _instance: "InMemoryCache | None" = None
    _lock = Lock()

    def __new__(cls) -> "InMemoryCache":
        """Singleton pattern - ensures single cache instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._store = {}
                    cls._instance._store_lock = Lock()
        return cls._instance

    def set(self, key: str, value: str, ttl_seconds: int = 600) -> None:
        """Store a value with TTL."""
        with self._store_lock:
            self._cleanup_expired()
            expires_at = time.time() + ttl_seconds
            self._store[key] = (value, expires_at)

    def get(self, key: str) -> str | None:
        """Get a value by key, returns None if expired or not found."""
        with self._store_lock:
            self._cleanup_expired()
            if key in self._store:
                value, expires_at = self._store[key]
                if time.time() < expires_at:
                    return value
                del self._store[key]
            return None

    def pop(self, key: str) -> str | None:
        """Get and remove a value by key."""
        with self._store_lock:
            self._cleanup_expired()
            if key in self._store:
                value, expires_at = self._store.pop(key)
                if time.time() < expires_at:
                    return value
            return None

    def delete(self, key: str) -> bool:
        """Delete a key, returns True if key existed."""
        with self._store_lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries."""
        with self._store_lock:
            self._store.clear()

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expires_at) in self._store.items()
            if current_time >= expires_at
        ]
        for key in expired_keys:
            del self._store[key]


# Singleton instance
cache = InMemoryCache()

