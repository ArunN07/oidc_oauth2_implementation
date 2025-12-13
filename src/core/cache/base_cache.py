from abc import ABC, abstractmethod


class BaseCache(ABC):
    """
    Abstract base class for cache implementations.

    Defines a consistent interface for all caching backends
    (e.g., Redis or in-memory). Concrete subclasses must
    implement retrieval, storage, deletion, clearing, and
    listing operations.
    """

    @abstractmethod
    def get(self, key: str) -> str | None:
        """
        Retrieve a value from the cache by its key.

        Parameters
        ----------
        key : str
            The key whose value should be fetched.

        Returns
        -------
        str | None
            The cached value if present and not expired; otherwise None.
        """

    @abstractmethod
    def set(self, key: str, value: str, expire: int = 3600) -> None:
        """
        Store a value in the cache with an optional expiration time.

        Parameters
        ----------
        key : str
            The cache key.
        value : str
            The value to store.
        expire : int, default=3600
            Time-to-live (seconds) before expiration.
        """

    @abstractmethod
    def delete(self, key: str) -> int:
        """
        Delete a key and its associated value.

        Parameters
        ----------
        key : str
            The cache key to delete.

        Returns
        -------
        int
            The number of keys deleted (0 or 1).
        """

    @abstractmethod
    def clear_all(self, pattern: str | None = None) -> int:
        """
        Clear all cache entries matching a given pattern.

        Parameters
        ----------
        pattern : str | None, default=None
            Wildcard pattern to match keys for deletion. If None, all entries are cleared.

        Returns
        -------
        int
            Number of keys deleted.
        """

    @abstractmethod
    def list_keys(self, pattern: str | None = None) -> list[str]:
        """
        List all keys currently present in the cache.

        Parameters
        ----------
        pattern : str | None, default=None
            Wildcard pattern for filtering keys.

        Returns
        -------
        list[str]
            List of matching cache keys.
        """
