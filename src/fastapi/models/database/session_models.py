"""
Database models for OAuth2/OIDC session tracking.

This module defines SQLModel classes for tracking user authentication sessions
and logging authentication attempts. These models demonstrate how to persist
OAuth2/OIDC authentication data for session management.

Classes
-------
UserSession
    Tracks active user authentication sessions with token metadata.
AuthenticationLog
    Logs all authentication attempts for auditing purposes.

Examples
--------
Creating a new session after successful authentication:

>>> session = UserSession(
...     user_id="12345",
...     provider="azure",
...     username="john.doe",
...     email="john@example.com",
...     access_token_hash="sha256hash...",
...     token_type="oidc",
...     has_id_token=True,
... )
>>> db.add(session)
>>> db.commit()
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    """
    Track user authentication sessions.

    This model stores session information for authenticated users, including
    token metadata (without storing actual tokens for security). It distinguishes
    between OAuth2-only sessions (access_token only) and OIDC sessions
    (access_token + id_token).

    Attributes
    ----------
    id : int | None
        Primary key, auto-generated.
    user_id : str
        Unique identifier from the identity provider (sub claim for OIDC).
    provider : str
        Authentication provider name ('github', 'azure', 'google').
    username : str | None
        User's display name or username.
    email : str | None
        User's email address.
    login_time : datetime
        Timestamp when the session was created.
    logout_time : datetime | None
        Timestamp when the session was ended (None if still active).
    is_active : bool
        Whether the session is currently active.
    access_token_hash : str
        SHA-256 hash of the access token (for lookup without storing token).
    token_type : str
        Type of authentication: 'oauth2' or 'oidc'.
    has_id_token : bool
        Whether an id_token was provided (True for OIDC providers).
    has_refresh_token : bool
        Whether a refresh_token was provided.
    expires_in : int | None
        Token expiration time in seconds.
    roles : str | None
        Comma-separated list of assigned roles.
    ip_address : str | None
        Client IP address for security auditing.
    user_agent : str | None
        Client user agent string.

    Notes
    -----
    - Access tokens are never stored directly; only a hash is kept for lookup.
    - The token_type field helps distinguish OAuth2-only vs OIDC sessions.
    - GitHub sessions will have has_id_token=False, has_refresh_token=False.
    - Azure/Google sessions will have has_id_token=True, has_refresh_token=True.
    """

    __tablename__ = "user_sessions"

    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: str = Field(max_length=255, index=True)
    provider: str = Field(max_length=50, index=True)
    username: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255, index=True)
    login_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    logout_time: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    access_token_hash: str = Field(max_length=64)
    token_type: str = Field(max_length=20)
    has_id_token: bool = Field(default=False)
    has_refresh_token: bool = Field(default=False)
    expires_in: int | None = Field(default=None)
    roles: str | None = Field(default=None, max_length=500)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None)

    def __repr__(self) -> str:
        """Return string representation of the session."""
        return (
            f"<UserSession(id={self.id}, user={self.username}, " f"provider={self.provider}, active={self.is_active})>"
        )


class AuthenticationLog(SQLModel, table=True):
    """
    Log all authentication attempts for auditing.

    This model records every authentication attempt, successful or failed,
    for security auditing and monitoring purposes.

    Attributes
    ----------
    id : int | None
        Primary key, auto-generated.
    provider : str
        Authentication provider name.
    user_id : str | None
        User identifier (None if authentication failed before identification).
    username : str | None
        Username (None if authentication failed before identification).
    success : bool
        Whether the authentication attempt was successful.
    error_message : str | None
        Error message if authentication failed.
    timestamp : datetime
        When the authentication attempt occurred.
    ip_address : str | None
        Client IP address.
    user_agent : str | None
        Client user agent string.

    Notes
    -----
    - Failed attempts may have null user_id/username if failure occurred early.
    - Use this log for security monitoring and detecting suspicious activity.
    """

    __tablename__ = "authentication_logs"

    id: int | None = Field(default=None, primary_key=True, index=True)
    provider: str = Field(max_length=50, index=True)
    user_id: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    success: bool = Field()
    error_message: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None)

    def __repr__(self) -> str:
        """Return string representation of the log entry."""
        return f"<AuthenticationLog(id={self.id}, provider={self.provider}, " f"success={self.success})>"
