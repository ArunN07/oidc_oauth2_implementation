"""
Azure AD OIDC authentication router.

This router handles the Azure AD OpenID Connect (OIDC) authorization code flow.
Azure AD fully supports OIDC, providing access_token, id_token, and refresh_token.

Protocol: OIDC (OpenID Connect)
- For pure OAuth2 flow, use /api/v1/auth/oauth2/azure/login instead.

Key Characteristics of Azure AD OIDC:
- Returns JWT access_token (can be used with Microsoft Graph API)
- Returns id_token (JWT containing user claims)
- Returns refresh_token (for obtaining new tokens)
- Supports JWKS validation of id_token
- User info available in id_token claims (no API call needed)

Endpoints
---------
GET /login
    Initiates the OIDC flow by redirecting to Azure AD.
GET /callback
    Handles the OIDC callback with authorization code.

Examples
--------
1. User visits /api/v1/auth/azure/login
2. Redirected to Microsoft login page
3. After consent, redirected back to /api/v1/auth/azure/callback
4. Server exchanges code for tokens (access_token + id_token + refresh_token)
5. User info extracted from id_token claims
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
from src.fastapi.services.auth.azure_service import AzureAuthService
from src.fastapi.services.auth.role_service import get_role_service
from src.fastapi.utilities.session_helpers import create_session_and_log, get_request_info, log_auth_failure
from src.fastapi.utilities.database import get_db

router = APIRouter(prefix="/azure", tags=["Azure OIDC"])


def get_azure_service() -> AzureAuthService:
    """Get Azure AD authentication service instance."""
    return AzureAuthService()



@router.get("/login")
async def azure_login(
    service: AzureAuthService = Depends(get_azure_service),
    logger: Logger = Depends(get_logger),
):
    """
    Initiate Azure AD OIDC login flow.

    Generates a state token for CSRF protection and redirects the user
    to Microsoft's authorization page. Uses prompt=consent to ensure
    refresh_token is returned.

    Returns
    -------
    RedirectResponse
        Redirect to Azure AD's authorization URL.
    """
    state = secrets.token_hex(16)
    auth_url = service.get_authorization_url(state=state)
    logger.info(f"Azure login initiated: state={state[:8]}...")

    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=AuthResponse)
async def azure_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Azure AD"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    service: AzureAuthService = Depends(get_azure_service),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
):
    """
    Handle Azure AD OIDC callback.

    Exchanges the authorization code for tokens, extracts user information
    from the id_token claims, creates a session, and returns the response.

    Parameters
    ----------
    request : Request
        FastAPI request object for extracting client info.
    code : str
        Authorization code received from Azure AD.
    state : str | None
        State parameter for CSRF validation.
    service : AzureAuthService
        Azure AD authentication service.
    db : Session
        Database session for storing session data.
    logger : Logger
        Logger instance.

    Returns
    -------
    AuthResponse
        Authentication response with tokens and user info.

    Raises
    ------
    HTTPException
        If token exchange fails.

    Notes
    -----
    Azure AD OIDC characteristics:
    - access_token: JWT for Microsoft Graph API
    - id_token: JWT with user claims (sub, name, email, groups)
    - refresh_token: For obtaining new tokens
    - expires_in: Token lifetime in seconds (typically 3600)
    """
    request_info = get_request_info(request)

    try:
        # Exchange authorization code for tokens
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            log_auth_failure(db, "azure", token_response.get("error_description", "Token exchange failed"), request_info)
            raise OAuth2CallbackError(message="Azure token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            log_auth_failure(db, "azure", "No access token in response", request_info)
            raise OAuth2CallbackError(message="No access token received")

        # Extract user info from id_token claims (no API call needed!)
        user_data = await service.get_user_from_token(token_response)

        # Assign roles based on configuration and Azure AD groups
        role_service = get_role_service()
        roles = role_service.get_user_roles("azure", user_data)
        groups = role_service.get_user_groups("azure", user_data)

        # Create unified user model
        unified_user = UnifiedUser.from_azure(user_data, roles, groups)

        # Create session and log authentication
        create_session_and_log(db, "azure", unified_user, token_response, request_info, roles)

        logger.info(f"Azure auth successful: {unified_user.username}, roles={roles}")

        return AuthResponse(
            access_token=access_token,
            token_type=token_response.get("token_type", "Bearer"),
            user=unified_user,
            id_token=token_response.get("id_token"),
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in"),
        )

    except OAuth2CallbackError:
        raise
    except Exception as e:
        log_auth_failure(db, "azure", str(e), request_info)
        logger.error(f"Azure callback error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
