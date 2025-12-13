import hashlib
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.models.database_models import AuthenticationLog, UserSession


class SessionService:
    """
    Manage user sessions and authentication logs.

    This service handles:
    - Creating and ending user sessions
    - Tracking login/logout times
    - Logging authentication attempts
    - Querying active sessions and auth logs

    Methods
    -------
    create_session(db, user_data, token_data, request_info)
        Create a new user session.
    end_session(db, session_id)
        End an active session.
    get_active_sessions(db, user_id, provider)
        Get all active sessions for a user.
    log_authentication(db, provider, user_id, success, error_msg, request_info)
        Log an authentication attempt.
    """

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash an access token for storage.

        Parameters
        ----------
        token : str
            Access token to hash.

        Returns
        -------
        str
            SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_session(
        db: Session,
        user_data: Dict[str, Any],
        token_data: Dict[str, Any],
        request_info: Optional[Dict[str, str]] = None,
    ) -> UserSession:
        """
        Create a new user session.

        Parameters
        ----------
        db : Session
            Database session.
        user_data : dict
            User information from provider.
        token_data : dict
            Token information (access_token, id_token, etc.).
        request_info : dict, optional
            Request metadata (ip_address, user_agent).

        Returns
        -------
        UserSession
            Created session record.
        """
        request_info = request_info or {}

        # Determine token type
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
    def end_session(db: Session, session_id: int) -> Optional[UserSession]:
        """
        End an active session.

        Parameters
        ----------
        db : Session
            Database session.
        session_id : int
            Session ID to end.

        Returns
        -------
        UserSession, optional
            Updated session record if found.
        """
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if session and session.is_active:
            session.logout_time = datetime.now(UTC)
            session.is_active = False
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def end_sessions_by_token(db: Session, access_token: str) -> List[UserSession]:
        """
        End all sessions with a specific access token.

        Parameters
        ----------
        db : Session
            Database session.
        access_token : str
            Access token to match.

        Returns
        -------
        list of UserSession
            Updated session records.
        """
        token_hash = SessionService._hash_token(access_token)
        sessions = (
            db.query(UserSession)
            .filter(UserSession.access_token_hash == token_hash, UserSession.is_active.is_(True))
            .all()
        )

        for session in sessions:
            session.logout_time = datetime.now(UTC)
            session.is_active = False

        db.commit()
        return sessions

    @staticmethod
    def get_active_sessions(
        db: Session, user_id: Optional[str] = None, provider: Optional[str] = None
    ) -> List[UserSession]:
        """
        Get active sessions, optionally filtered by user and/or provider.

        Parameters
        ----------
        db : Session
            Database session.
        user_id : str, optional
            Filter by user ID.
        provider : str, optional
            Filter by provider.

        Returns
        -------
        list of UserSession
            Active sessions matching criteria.
        """
        query = db.query(UserSession).filter(UserSession.is_active.is_(True))

        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        if provider:
            query = query.filter(UserSession.provider == provider)

        return query.all()

    @staticmethod
    def log_authentication(
        db: Session,
        provider: str,
        user_id: Optional[str],
        username: Optional[str],
        success: bool,
        error_msg: Optional[str] = None,
        request_info: Optional[Dict[str, str]] = None,
    ) -> AuthenticationLog:
        """
        Log an authentication attempt.

        Parameters
        ----------
        db : Session
            Database session.
        provider : str
            Authentication provider.
        user_id : str, optional
            User identifier if successful.
        username : str, optional
            Username if available.
        success : bool
            Whether authentication succeeded.
        error_msg : str, optional
            Error message if failed.
        request_info : dict, optional
            Request metadata.

        Returns
        -------
        AuthenticationLog
            Created log record.
        """
        request_info = request_info or {}

        log = AuthenticationLog(
            provider=provider,
            user_id=user_id,
            username=username,
            success=success,
            error_message=error_msg,
            timestamp=datetime.now(UTC),
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
        )

        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_authentication_logs(
        db: Session, provider: Optional[str] = None, user_id: Optional[str] = None, limit: int = 100
    ) -> List[AuthenticationLog]:
        """
        Get authentication logs with optional filters.

        Parameters
        ----------
        db : Session
            Database session.
        provider : str, optional
            Filter by provider.
        user_id : str, optional
            Filter by user ID.
        limit : int
            Maximum records to return.

        Returns
        -------
        list of AuthenticationLog
            Authentication logs.
        """
        query = db.query(AuthenticationLog).order_by(AuthenticationLog.timestamp.desc())

        if provider:
            query = query.filter(AuthenticationLog.provider == provider)
        if user_id:
            query = query.filter(AuthenticationLog.user_id == user_id)

        return query.limit(limit).all()
