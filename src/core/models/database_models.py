from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    """
    Track user authentication sessions.

    Attributes
    ----------
    id : int, optional
        Primary key (auto-generated).
    user_id : str
        User identifier from provider.
    provider : str
        Authentication provider (github, azure, google).
    username : str, optional
        Username or email.
    email : str, optional
        User email.
    login_time : datetime
        When user logged in (UTC).
    logout_time : datetime, optional
        When user logged out (UTC).
    is_active : bool
        Whether session is currently active.
    access_token_hash : str
        Hashed access token for validation.
    token_type : str
        Type of authentication (oauth2 or oidc).
    has_id_token : bool
        Whether OIDC id_token was provided.
    has_refresh_token : bool
        Whether refresh_token was provided.
    expires_in : int, optional
        Token expiration time in seconds.
    roles : str, optional
        Comma-separated user roles.
    ip_address : str, optional
        Client IP address.
    user_agent : str, optional
        Client user agent string.
    """

    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: str = Field(max_length=255, index=True)
    provider: str = Field(max_length=50, index=True)
    username: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255, index=True)
    login_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    logout_time: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    access_token_hash: str = Field(max_length=64)
    token_type: str = Field(max_length=20)  # 'oauth2' or 'oidc'
    has_id_token: bool = Field(default=False)
    has_refresh_token: bool = Field(default=False)
    expires_in: Optional[int] = Field(default=None)
    roles: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)

    def __repr__(self) -> str:
        """String representation of UserSession."""
        return f"<UserSession(id={self.id}, user={self.username}, provider={self.provider}, active={self.is_active})>"


class AuthenticationLog(SQLModel, table=True):
    """
    Log all authentication attempts.

    Attributes
    ----------
    id : int, optional
        Primary key (auto-generated).
    provider : str
        Authentication provider.
    user_id : str, optional
        User identifier if successful.
    username : str, optional
        Username if available.
    success : bool
        Whether authentication succeeded.
    error_message : str, optional
        Error message if failed.
    timestamp : datetime
        When authentication was attempted (UTC).
    ip_address : str, optional
        Client IP address.
    user_agent : str, optional
        Client user agent string.
    """

    __tablename__ = "authentication_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    provider: str = Field(max_length=50, index=True)
    user_id: Optional[str] = Field(default=None, max_length=255)
    username: Optional[str] = Field(default=None, max_length=255)
    success: bool = Field()
    error_message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)

    def __repr__(self) -> str:
        """String representation of AuthenticationLog."""
        return f"<AuthenticationLog(id={self.id}, provider={self.provider}, success={self.success})>"
