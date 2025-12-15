"""
Session management service for OAuth2/OIDC authentication.

This module provides the SessionService class for managing user authentication
sessions in the database. It handles session creation, termination, and
authentication logging.

The service demonstrates proper session tracking for OAuth2/OIDC flows:
- Creates sessions after successful authentication
- Tracks token metadata (without storing actual tokens)
- Distinguishes between OAuth2-only and OIDC sessions
- Logs all authentication attempts for auditing

Examples
--------
Creating a session after successful authentication:

>>> from fastapi import Depends
>>> from sqlmodel import Session
>>> from src.fastapi.services.database import SessionService
>>>
>>> async def callback(db: Session = Depends(get_db)):
...     user_data = {"id": "123", "provider": "azure", "email": "user@example.com"}
...     token_data = {"access_token": "abc123", "id_token": "xyz789"}
...     session = SessionService.create_session(db, user_data, token_data)
...     return session
"""

import hashlib
from datetime import UTC, datetime
from logging import Logger
from typing import Any

from sqlmodel import Session

from src.fastapi.models.database.session_models import AuthenticationLog, UserSession


class SessionService:
    """
    Service for managing user authentication sessions.

    This service provides static methods for creating, ending, and querying
    user sessions. It also handles authentication logging for security auditing.

    Methods
    -------
    create_session(db, user_data, token_data, request_info)
        Create a new user session after successful authentication.
    end_session(db, session_id)
        End an active session by ID.
    end_sessions_by_token(db, access_token)
        End all sessions matching a specific access token.
    get_active_sessions(db, user_id, provider)
        Get all active sessions for a user.
    log_authentication(db, provider, user_id, success, error_msg, request_info)
        Log an authentication attempt.

    Notes
    -----
    - Access tokens are hashed using SHA-256 before storage.
    - The service automatically determines if a session is OIDC or OAuth2
      based on the presence of an id_token.
    """

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash an access token for secure storage.

        Parameters
        ----------
        token : str
            The access token to hash.

        Returns
        -------
        str
            SHA-256 hash of the token (64 characters).

        Notes
        -----
        We store a hash rather than the actual token for security.
        This allows session lookup without exposing the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_session(
        db: Session,
        user_data: dict[str, Any],
        token_data: dict[str, Any],
        request_info: dict[str, str] | None = None,
    ) -> UserSession:
        """
        Create a new user session after successful authentication.

        Parameters
        ----------
        db : Session
            SQLModel database session.
        user_data : dict[str, Any]
            User information from the identity provider. Expected keys:
            - id: User's unique identifier
            - provider: Provider name ('github', 'azure', 'google')
            - username: User's display name (optional)
            - email: User's email address (optional)
            - roles: List of assigned roles (optional)
        token_data : dict[str, Any]
            Token response from the identity provider. Expected keys:
            - access_token: The OAuth2 access token
            - id_token: The OIDC id_token (optional, OIDC only)
            - refresh_token: Refresh token (optional)
            - expires_in: Token expiration in seconds (optional)
        request_info : dict[str, str] | None, optional
            Request metadata for security auditing. Expected keys:
            - ip_address: Client IP address
            - user_agent: Client user agent string

        Returns
        -------
        UserSession
            The created session record.

        Examples
        --------
        >>> user_data = {
        ...     "id": "aO0DyTtK...",
        ...     "provider": "azure",
        ...     "username": "John Doe",
        ...     "email": "john@example.com",
        ...     "roles": ["user", "admin"]
        ... }
        >>> token_data = {
        ...     "access_token": "eyJ0eXAi...",
        ...     "id_token": "eyJ0eXAi...",
        ...     "refresh_token": "0.AVYA...",
        ...     "expires_in": 3600
        ... }
        >>> session = SessionService.create_session(db, user_data, token_data)
        """
        request_info = request_info or {}

        # Determine token type based on presence of id_token
        has_id_token = token_data.get("id_token") is not None
        token_type = "oidc" if has_id_token else "oauth2"

        session = UserSession(
            user_id=str(user_data.get("id", "")),
            provider=user_data.get("provider", "unknown"),
            username=user_data.get("username"),
            email=user_data.get("email"),
            login_time=datetime.now(UTC),
            is_active=True,
            access_token_hash=SessionService._hash_token(token_data.get("access_token", "")),
            token_type=token_type,
            has_id_token=has_id_token,
            has_refresh_token=token_data.get("refresh_token") is not None,
            expires_in=token_data.get("expires_in"),
            roles=",".join(user_data.get("roles", [])),
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
        )

        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def end_session(db: Session, session_id: int) -> UserSession | None:
        """
        End an active session by ID.

        Parameters
        ----------
        db : Session
            SQLModel database session.
        session_id : int
            The session ID to end.

        Returns
        -------
        UserSession | None
            The updated session record if found and was active, None otherwise.
        """
        session = db.query(UserSession).filter(UserSession.id == session_id).first()  # type: ignore[arg-type]
        if session and session.is_active:
            session.logout_time = datetime.now(UTC)
            session.is_active = False
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def end_sessions_by_token(db: Session, access_token: str) -> list[UserSession]:
        """
        End all sessions matching a specific access token.

        Parameters
        ----------
        db : Session
            SQLModel database session.
        access_token : str
            The access token to match (will be hashed for lookup).

        Returns
        -------
        list[UserSession]
            List of ended session records.
        """
        token_hash = SessionService._hash_token(access_token)
        sessions = (
            db.query(UserSession)
            .filter(
                UserSession.access_token_hash == token_hash,  # type: ignore[arg-type]
                # pylint: disable=singleton-comparison
                UserSession.is_active == True,  # type: ignore[arg-type]  # noqa: E712
            )
            .all()
        )

        for session in sessions:
            session.logout_time = datetime.now(UTC)
            session.is_active = False

        if sessions:
            db.commit()

        return sessions

    @staticmethod
    def get_active_sessions(db: Session, user_id: str | None = None, provider: str | None = None) -> list[UserSession]:
        """
        Get active sessions, optionally filtered by user or provider.

        Parameters
        ----------
        db : Session
            SQLModel database session.
        user_id : str | None, optional
            Filter by user ID.
        provider : str | None, optional
            Filter by provider name.

        Returns
        -------
        list[UserSession]
            List of active session records.
        """
        query = db.query(UserSession).filter(
            UserSession.is_active == True  # type: ignore[arg-type]  # noqa: E712  # pylint: disable=singleton-comparison
        )

        if user_id:
            query = query.filter(UserSession.user_id == user_id)  # type: ignore[arg-type]
        if provider:
            query = query.filter(UserSession.provider == provider)  # type: ignore[arg-type]

        return query.all()

    @staticmethod
    def log_authentication(
        db: Session,
        provider: str,
        success: bool,
        user_id: str | None = None,
        username: str | None = None,
        error_message: str | None = None,
        request_info: dict[str, str] | None = None,
        logger: Logger | None = None,
    ) -> AuthenticationLog:
        """
        Log an authentication attempt.

        Parameters
        ----------
        db : Session
            SQLModel database session.
        provider : str
            Provider name ('github', 'azure', 'google').
        success : bool
            Whether the authentication was successful.
        user_id : str | None, optional
            User ID if available.
        username : str | None, optional
            Username if available.
        error_message : str | None, optional
            Error message if authentication failed.
        request_info : dict[str, str] | None, optional
            Request metadata (ip_address, user_agent).
        logger : Logger | None, optional
            Logger instance for logging the attempt.

        Returns
        -------
        AuthenticationLog
            The created log entry.
        """
        request_info = request_info or {}

        log_entry = AuthenticationLog(
            provider=provider,
            user_id=user_id,
            username=username,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(UTC),
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        if logger:
            if success:
                logger.info(f"Auth success: {provider} user={username or user_id}")
            else:
                logger.warning(f"Auth failed: {provider} user={username or user_id} " f"error={error_message}")

        return log_entry
