"""
GitHub Authentication Models.

This module provides Pydantic models for GitHub OAuth2
token responses and user information.
"""

from typing import Literal

from pydantic import BaseModel


class GitHubTokenResponse(BaseModel):
    """GitHub OAuth2 token response model."""

    access_token: str
    token_type: str = "bearer"
    scope: str


class GitHubUser(BaseModel):
    """GitHub user information - essential fields only."""

    id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class GitHubEmail(BaseModel):
    """GitHub email information."""

    email: str
    primary: bool
    verified: bool
    visibility: str | None = None


class GitHubLoginResponse(BaseModel):
    """Response for GitHub login endpoint."""

    authorization_url: str
    state: str | None = None


class GitHubCallbackResponse(BaseModel):
    """Response for GitHub callback endpoint."""

    access_token: str
    token_type: str
    user: GitHubUser


class GitHubUserResponse(BaseModel):
    """Response for GitHub /me endpoint."""

    provider: Literal["github"] = "github"
    user: GitHubUser
    emails: list[GitHubEmail] | None = None
    roles: list[str] = []
