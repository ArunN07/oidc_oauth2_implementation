"""PKCE State Storage for OAuth2/OIDC flows using in-memory cache."""

from src.core.cache.memory_cache import cache

PKCE_PREFIX = "pkce:"
PKCE_TTL_SECONDS = 600


def store_pkce_verifier(state: str, code_verifier: str) -> None:
    """Store a PKCE code_verifier for a given state."""
    cache.set(f"{PKCE_PREFIX}{state}", code_verifier, PKCE_TTL_SECONDS)


def retrieve_pkce_verifier(state: str) -> str | None:
    """Retrieve and remove a PKCE code_verifier for a given state."""
    return cache.pop(f"{PKCE_PREFIX}{state}")


# Backward compatibility - class-based interface
class PKCEStore:
    """PKCE store using shared in-memory cache."""

    def store(self, state: str, code_verifier: str) -> None:
        """Store a code_verifier for a given state."""
        store_pkce_verifier(state, code_verifier)

    def retrieve(self, state: str) -> str | None:
        """Retrieve and remove a code_verifier for a given state."""
        return retrieve_pkce_verifier(state)


# Singleton instance for backward compatibility
_pkce_store_instance = PKCEStore()


def get_pkce_store() -> PKCEStore:
    """Get the PKCE store instance."""
    return _pkce_store_instance
