from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    """
    Track user authentication sessions.
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
        return f"<UserSession(id={self.id}, user={self.username}, provider={self.provider}, active={self.is_active})>"


class AuthenticationLog(SQLModel, table=True):
    """
    Log all authentication attempts.
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
        return f"<AuthenticationLog(id={self.id}, provider={self.provider}, success={self.success})>"
