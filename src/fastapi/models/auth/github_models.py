from typing import List, Optional

from pydantic import BaseModel


class GitHubTokenResponse(BaseModel):
    """GitHub OAuth2 token response model."""

    access_token: str
    token_type: str = "bearer"
    scope: str


class GitHubUser(BaseModel):
    """GitHub user information."""

    id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    public_repos: Optional[int] = None
    followers: Optional[int] = None
    following: Optional[int] = None


class GitHubEmail(BaseModel):
    """GitHub email information."""

    email: str
    primary: bool
    verified: bool
    visibility: Optional[str] = None


class GitHubLoginResponse(BaseModel):
    """Response for GitHub login endpoint."""

    authorization_url: str
    state: Optional[str] = None


class GitHubCallbackResponse(BaseModel):
    """Response for GitHub callback endpoint."""

    access_token: str
    token_type: str
    user: GitHubUser


class GitHubUserResponse(BaseModel):
    """Response for GitHub /me endpoint."""

    provider: str = "github"
    user: GitHubUser
    emails: Optional[List[GitHubEmail]] = None
    roles: List[str] = []
