"""
GitHub OAuth2 authentication router.

This router handles the GitHub OAuth2 authorization code flow.
GitHub only supports OAuth2 (not OIDC), so it returns only an access_token
with no id_token or refresh_token.

Protocol: OAuth2 (GitHub does NOT support OIDC)

Key Characteristics of GitHub OAuth2:
- Returns opaque access_token (not a JWT)
- No id_token (GitHub doesn't support OIDC)
- No refresh_token (tokens don't expire until revoked)
- Requires API call to get user information

Endpoints
---------
GET /login
    Initiates the OAuth2 flow by redirecting to GitHub.
GET /callback
    Handles the OAuth2 callback with authorization code.

Examples
--------
1. User visits /api/v1/auth/github/login
2. Redirected to GitHub for authentication
3. After consent, redirected back to /api/v1/auth/github/callback
4. Server exchanges code for access_token
5. Server fetches user info via GitHub API
6. Session created and response returned
"""

import secrets
from logging import Logger

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.github_service import GitHubAuthService
from src.fastapi.services.auth.role_service import get_role_service
from src.fastapi.utilities.session_helpers import create_session_and_log, get_request_info, log_auth_failure
from src.fastapi.utilities.database import get_db

router = APIRouter(prefix="/github", tags=["GitHub OAuth2"])


def get_github_service() -> GitHubAuthService:
    """Get GitHub authentication service instance."""
    return GitHubAuthService()



@router.get("/login")
async def github_login(
    service: GitHubAuthService = Depends(get_github_service),
    logger: Logger = Depends(get_logger),
):
    """
    Initiate GitHub OAuth2 login flow.

    Generates a state token for CSRF protection and redirects the user
    to GitHub's authorization page.

    Returns
    -------
    RedirectResponse
        Redirect to GitHub's authorization URL.
    """
    state = secrets.token_hex(16)
    auth_url = service.get_authorization_url(state=state)
    logger.info(f"GitHub login initiated: state={state[:8]}...")

    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=AuthResponse)
async def github_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    service: GitHubAuthService = Depends(get_github_service),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
):
    """
    Handle GitHub OAuth2 callback.

    Exchanges the authorization code for an access token, fetches user
    information, creates a session, and returns the authentication response.

    Parameters
    ----------
    request : Request
        FastAPI request object for extracting client info.
    code : str
        Authorization code received from GitHub.
    state : str | None
        State parameter for CSRF validation.
    service : GitHubAuthService
        GitHub authentication service.
    db : Session
        Database session for storing session data.
    logger : Logger
        Logger instance.

    Returns
    -------
    AuthResponse
        Authentication response with access_token and user info.

    Raises
    ------
    HTTPException
        If token exchange or user info retrieval fails.

    Notes
    -----
    GitHub OAuth2 characteristics:
    - access_token: Opaque string (gho_xxx format)
    - id_token: None (GitHub doesn't support OIDC)
    - refresh_token: None (GitHub tokens don't expire)
    """
    request_info = get_request_info(request)

    try:
        # Exchange authorization code for access token
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            log_auth_failure(db, "github", token_response.get("error_description", "Token exchange failed"), request_info)
            raise OAuth2CallbackError(message="GitHub token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            log_auth_failure(db, "github", "No access token in response", request_info)
            raise OAuth2CallbackError(message="No access token received")

        # Fetch user info via GitHub API (required for OAuth2-only flow)
        user_data = await service.get_user_with_orgs(access_token)

        # Assign roles based on configuration
        role_service = get_role_service()
        roles = role_service.get_user_roles("github", user_data)
        groups = role_service.get_user_groups("github", user_data)

        # Create unified user model
        unified_user = UnifiedUser.from_github(user_data, roles, groups)

        # Create session and log authentication
        create_session_and_log(db, "github", unified_user, token_response, request_info, roles)

        logger.info(f"GitHub auth successful: {unified_user.username}, roles={roles}")

        return AuthResponse(
            access_token=access_token,
            token_type=token_response.get("token_type", "bearer"),
            user=unified_user,
            id_token=None,  # GitHub doesn't support OIDC
            refresh_token=None,  # GitHub doesn't provide refresh tokens
            expires_in=None,  # GitHub tokens don't expire
        )

    except OAuth2CallbackError:
        raise
    except Exception as e:
        log_auth_failure(db, "github", str(e), request_info)
        logger.error(f"GitHub callback error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
