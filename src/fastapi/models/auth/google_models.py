from typing import Optional

from pydantic import BaseModel, Field


class GoogleTokenResponse(BaseModel):
    """Google OAuth2/OIDC token response model."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class GoogleUser(BaseModel):
    """Google user information."""

    sub: str = Field(..., description="Subject identifier")
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


class GoogleIdTokenClaims(BaseModel):
    """Claims from Google ID token."""

    iss: str
    sub: str
    aud: str
    exp: int
    iat: int
    azp: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    locale: Optional[str] = None


class GoogleLoginResponse(BaseModel):
    """Response for Google login endpoint."""

    authorization_url: str
    state: Optional[str] = None


class GoogleCallbackResponse(BaseModel):
    """Response for Google callback endpoint."""

    access_token: str
    token_type: str
    expires_in: int
    id_token: Optional[str] = None
    user: GoogleUser


class GoogleUserResponse(BaseModel):
    """Response for Google /me endpoint."""

    provider: str = "google"
    user: GoogleUser
    claims: Optional[GoogleIdTokenClaims] = None
