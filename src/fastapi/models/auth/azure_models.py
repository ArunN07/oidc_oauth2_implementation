from typing import List, Optional

from pydantic import BaseModel, Field


class AzureTokenResponse(BaseModel):
    """Azure AD OAuth2/OIDC token response model."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class AzureUser(BaseModel):
    """Azure AD user information from ID token or Graph API."""

    sub: str = Field(..., description="Subject identifier")
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    oid: Optional[str] = Field(None, description="Object ID in Azure AD")
    tid: Optional[str] = Field(None, description="Tenant ID")
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    roles: Optional[List[str]] = None


class AzureIdTokenClaims(BaseModel):
    """Claims from Azure AD ID token."""

    iss: str
    sub: str
    aud: str
    exp: int
    iat: int
    nbf: Optional[int] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    email: Optional[str] = None
    oid: Optional[str] = None
    tid: Optional[str] = None
    roles: Optional[List[str]] = None
    groups: Optional[List[str]] = None


class AzureLoginResponse(BaseModel):
    """Response for Azure login endpoint."""

    authorization_url: str
    state: Optional[str] = None


class AzureCallbackResponse(BaseModel):
    """Response for Azure callback endpoint."""

    access_token: str
    token_type: str
    expires_in: int
    id_token: Optional[str] = None
    user: AzureUser


class AzureUserResponse(BaseModel):
    """Response for Azure /me endpoint."""

    provider: str = "azure"
    user: AzureUser
    claims: Optional[AzureIdTokenClaims] = None
