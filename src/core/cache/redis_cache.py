import redis
from redis import ConnectionPool, Redis

from delphi_studio_backend.core.cache.base_cache import BaseCache


class RedisCache(BaseCache):
    """
    Redis-based cache backend using the `redis` Python client.

    Provides persistent and distributed caching capabilities with TTL support.

    Parameters
    ----------
    redis_url : str
        Redis connection string (e.g., redis://[:password]@host:port/db).
    """

    def __init__(self, redis_url: str):
        self.pool = ConnectionPool.from_url(redis_url, max_connections=10, decode_responses=True)
        self.client = Redis(connection_pool=self.pool)

    def get(self, key: str) -> str | None:
        """Retrieve a value from Redis by key."""
        return self.client.get(key)

    def set(self, key: str, value: str, expire: int | None = None) -> None:
        """Store a key-value pair in Redis with an optional TTL."""
        if expire is None:
            self.client.set(key, value)
        else:
            self.client.set(key, value, ex=expire)

    def delete(self, key: str) -> int:
        """
        Delete a specific Redis key.

        Parameters
        ----------
        key : str
            Cache key to delete.

        Returns
        -------
        int
            Number of keys deleted (0 or 1).
        """
        return self.client.delete(key)

    def clear_all(self, pattern: str | None = None) -> int:
        """
        Clear all or matching Redis keys.

        Parameters
        ----------
        pattern : str, optional
            Wildcard pattern for matching keys.

        Returns
        -------
        int
            Number of deleted keys.
        """
        if pattern:
            return self._delete_by_pattern(pattern)
        try:
            deleted_count = self.client.dbsize()
            self.client.flushdb()
            return deleted_count
        except redis.exceptions.ResponseError:
            # Fallback if FLUSHDB not permitted
            return self._delete_by_pattern("*")

    def _delete_by_pattern(self, pattern: str) -> int:
        """
        Delete keys matching a pattern using SCAN and DELETE.

        Parameters
        ----------
        pattern : str
            Wildcard pattern to match keys.

        Returns
        -------
        int
            Number of deleted keys.
        """
        keys_to_delete = list(self.client.scan_iter(match=pattern))
        return self.client.delete(*keys_to_delete) if keys_to_delete else 0

    def list_keys(self, pattern: str | None = None) -> list[str]:
        """
        List all keys in Redis cache, optionally filtered by pattern.

        Parameters
        ----------
        pattern : str, optional
            Wildcard pattern to match keys.

        Returns
        -------
        list of str
            List of keys matching the pattern.
        """
        pattern = pattern or "*"
        return list(self.client.scan_iter(match=pattern))
