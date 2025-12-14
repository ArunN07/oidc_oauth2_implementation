"""
PKCE State Storage for OAuth2/OIDC flows.

This module provides secure storage for PKCE (Proof Key for Code Exchange)
code_verifiers during the OAuth2 authorization flow. The code_verifier must
be stored between the authorization request and the token exchange.

Why PKCE Storage is Needed:
--------------------------
1. **Two-Step Process**: Authorization and token exchange are separate requests
2. **Security**: code_verifier must be kept secret and retrieved exactly once
3. **State Binding**: code_verifier is bound to the state parameter for security

How PKCE Works:
--------------
1. Generate random code_verifier
2. Create code_challenge = SHA256(code_verifier)
3. Send code_challenge in authorization request
4. Store code_verifier keyed by state
5. On callback, retrieve code_verifier using state
6. Send code_verifier in token request
7. Provider verifies SHA256(code_verifier) == code_challenge

Cache Usage:
-----------
Uses in-memory cache with TTL for automatic cleanup:
- TTL: 600 seconds (10 minutes) - enough for user to authenticate
- Automatic expiration prevents memory leaks
- Pop-on-retrieve ensures one-time use

Functions
---------
store_pkce_verifier
    Store a code_verifier for a given state.
retrieve_pkce_verifier
    Retrieve and remove a code_verifier.
get_pkce_store
    Get the PKCEStore singleton instance.

Examples
--------
Storing and retrieving a PKCE verifier:

>>> from src.core.auth.pkce_store import store_pkce_verifier, retrieve_pkce_verifier
>>>
>>> # During authorization request
>>> state = "random_state_123"
>>> code_verifier = "random_verifier_456"
>>> store_pkce_verifier(state, code_verifier)
>>>
>>> # During token exchange (callback)
>>> verifier = retrieve_pkce_verifier(state)
>>> assert verifier == "random_verifier_456"
>>>
>>> # Second retrieval returns None (one-time use)
>>> assert retrieve_pkce_verifier(state) is None
"""

from src.core.cache.memory_cache import cache

PKCE_PREFIX = "pkce:"
PKCE_TTL_SECONDS = 600  # 10 minutes - enough for user authentication


def store_pkce_verifier(state: str, code_verifier: str) -> None:
    """
    Store a PKCE code_verifier for a given state.

    Parameters
    ----------
    state : str
        The state parameter used in the authorization request.
    code_verifier : str
        The PKCE code_verifier to store.

    Notes
    -----
    - Stored with PKCE_TTL_SECONDS (600s) TTL for automatic cleanup
    - Key format: "pkce:{state}"
    """
    cache.set(f"{PKCE_PREFIX}{state}", code_verifier, PKCE_TTL_SECONDS)


def retrieve_pkce_verifier(state: str) -> str | None:
    """
    Retrieve and remove a PKCE code_verifier for a given state.

    Parameters
    ----------
    state : str
        The state parameter from the callback.

    Returns
    -------
    str | None
        The code_verifier if found, None otherwise.

    Notes
    -----
    - Uses pop() for one-time retrieval (security best practice)
    - Returns None if expired or not found
    """
    return cache.pop(f"{PKCE_PREFIX}{state}")


class PKCEStore:
    """
    Class-based PKCE store for backward compatibility.

    Wraps the function-based API in a class interface.
    Use the module-level functions for new code.

    Methods
    -------
    store(state, code_verifier)
        Store a code_verifier.
    retrieve(state)
        Retrieve and remove a code_verifier.
    """

    def store(self, state: str, code_verifier: str) -> None:
        """Store a code_verifier for a given state."""
        store_pkce_verifier(state, code_verifier)

    def retrieve(self, state: str) -> str | None:
        """Retrieve and remove a code_verifier for a given state."""
        return retrieve_pkce_verifier(state)


# Singleton instance for backward compatibility
_pkce_store_instance = PKCEStore()


def get_pkce_store() -> PKCEStore:
    """
    Get the PKCE store singleton instance.

    Returns
    -------
    PKCEStore
        The singleton PKCEStore instance.
    """
    return _pkce_store_instance
