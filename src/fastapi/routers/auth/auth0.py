"""
Auth0 OIDC authentication router.

Protocol: OIDC (OpenID Connect)
- For pure OAuth2 flow, use /api/v1/auth/oauth2/auth0/login instead.

Endpoints
---------
GET /login
    Initiates the OIDC flow by redirecting to Auth0.
GET /callback
    Handles the OIDC callback with authorization code.
"""

import secrets
from logging import Logger

from sqlmodel import Session

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.auth0_service import Auth0AuthService
from src.fastapi.services.auth.role_service import get_role_service
from src.fastapi.utilities.database import get_db
from src.fastapi.utilities.session_helpers import create_session_and_log, get_request_info, log_auth_failure

router = APIRouter(prefix="/auth0", tags=["Auth0 OIDC"])


def get_auth0_service() -> Auth0AuthService:
    """Get Auth0 authentication service instance."""
    return Auth0AuthService()


@router.get("/login")
async def auth0_login(
    service: Auth0AuthService = Depends(get_auth0_service),
    logger: Logger = Depends(get_logger),
) -> RedirectResponse:
    """
    Initiate Auth0 OIDC login flow.

    Redirects the user to Auth0 for authentication.
    """
    state = secrets.token_hex(16)
    auth_url = service.get_authorization_url(state=state)
    logger.info(f"Auth0 login initiated, state={state[:8]}...")
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=AuthResponse)
async def auth0_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Auth0"),
    state: str | None = Query(None, description="State parameter for CSRF validation"),
    service: Auth0AuthService = Depends(get_auth0_service),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> AuthResponse:
    """
    Handle Auth0 OIDC callback.

    Exchanges the authorization code for tokens and creates a user session.
    """
    request_info = get_request_info(request)

    try:
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            log_auth_failure(db, "auth0", token_response.get("error_description", "Token exchange failed"), request_info)
            raise OAuth2CallbackError(message="Auth0 token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            log_auth_failure(db, "auth0", "No access token in response", request_info)
            raise OAuth2CallbackError(message="No access token received")

        user_data = await service.get_user_from_token(token_response)

        role_service = get_role_service()
        roles = role_service.get_user_roles("auth0", user_data)
        groups = role_service.get_user_groups("auth0", user_data)

        unified_user = UnifiedUser.from_auth0(user_data, roles, groups)

        create_session_and_log(db, "auth0", unified_user, token_response, request_info, roles)

        logger.info(f"Auth0 auth successful: {unified_user.email}, roles={roles}")

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
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_auth_failure(db, "auth0", str(e), request_info)
        logger.error("Auth0 callback error: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
