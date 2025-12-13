from enum import Enum


class CacheType(str, Enum):
    """
    Enumeration of supported cache backends.

    Attributes
    ----------
    MEMORY : str
        In-memory cache backend.
    REDIS : str
        Redis-based cache backend.
    """

    MEMORY = "memory"
    REDIS = "redis"
