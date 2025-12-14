from typing import Literal

from pydantic import BaseModel, Field


class AzureTokenResponse(BaseModel):
    """Azure AD OAuth2/OIDC token response model."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    refresh_token: str | None = None
    id_token: str | None = None


class AzureUser(BaseModel):
    """Azure AD user information - essential fields only."""

    sub: str = Field(..., description="Subject identifier")
    name: str | None = None
    email: str | None = None
    preferred_username: str | None = None


class AzureIdTokenClaims(BaseModel):
    """Essential claims from Azure AD ID token."""

    iss: str
    sub: str
    aud: str
    exp: int
    name: str | None = None
    email: str | None = None
    preferred_username: str | None = None


class AzureLoginResponse(BaseModel):
    """Response for Azure login endpoint."""

    authorization_url: str
    state: str | None = None


class AzureCallbackResponse(BaseModel):
    """Response for Azure callback endpoint."""

    access_token: str
    token_type: str
    expires_in: int
    id_token: str | None = None
    user: AzureUser


class AzureUserResponse(BaseModel):
    """Response for Azure /me endpoint."""

    provider: Literal["azure"] = "azure"
    user: AzureUser
    claims: AzureIdTokenClaims | None = None
