from typing import Literal

from pydantic import BaseModel, Field


class GoogleTokenResponse(BaseModel):
    """Google OAuth2/OIDC token response model."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    refresh_token: str | None = None
    id_token: str | None = None


class GoogleUser(BaseModel):
    """Google user information - essential fields only."""

    sub: str = Field(..., description="Subject identifier")
    name: str | None = None
    email: str | None = None
    email_verified: bool | None = None
    picture: str | None = None


class GoogleIdTokenClaims(BaseModel):
    """Essential claims from Google ID token."""

    iss: str
    sub: str
    aud: str
    exp: int
    email: str | None = None
    email_verified: bool | None = None
    name: str | None = None
    picture: str | None = None


class GoogleLoginResponse(BaseModel):
    """Response for Google login endpoint."""

    authorization_url: str
    state: str | None = None


class GoogleCallbackResponse(BaseModel):
    """Response for Google callback endpoint."""

    access_token: str
    token_type: str
    expires_in: int
    id_token: str | None = None
    user: GoogleUser


class GoogleUserResponse(BaseModel):
    """Response for Google /me endpoint."""

    provider: Literal["google"] = "google"
    user: GoogleUser
    claims: GoogleIdTokenClaims | None = None
