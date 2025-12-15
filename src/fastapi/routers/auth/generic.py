"""
Generic OAuth2 vs OIDC comparison router.

This router provides side-by-side comparison of OAuth2 and OIDC flows
for Azure and Google providers. It demonstrates the key differences:

OAuth2 Flow (/oauth2/{provider}/login):
- Returns only access_token
- No id_token (must call API for user info)
- No refresh_token (without offline_access scope)

OIDC Flow (/oidc/{provider}/login):
- Returns access_token + id_token + refresh_token
- User info in id_token claims (no API call needed)
- Supports token refresh

Also provides:
- /providers: List all providers and their capabilities
- /logout: End session using bearer token (works with any provider)
"""

import secrets
from logging import Logger
from typing import Any, cast
from urllib.parse import urlencode

from sqlmodel import Session

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from src.core.auth.base import BaseAuthProvider
from src.core.auth.http_client import get_http_client
from src.core.auth.security import bearer_scheme
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.core.settings.app import AuthProvider, get_settings
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.auth0_service import Auth0AuthService
from src.fastapi.services.auth.azure_service import AzureAuthService
from src.fastapi.services.auth.github_service import GitHubAuthService
from src.fastapi.services.auth.google_service import GoogleAuthService
from src.fastapi.services.auth.role_service import get_role_service
from src.fastapi.services.database.session_service import SessionService
from src.fastapi.utilities.database import get_db
from src.fastapi.utilities.session_helpers import create_session_and_log, get_request_info, log_auth_failure, log_logout

router = APIRouter(tags=["OAuth2 vs OIDC Comparison"])

_state_map: dict[str, dict[str, str]] = {}


def _get_service(provider: AuthProvider) -> BaseAuthProvider:
    """Get the appropriate auth service for a provider."""
    services: dict[AuthProvider, type[BaseAuthProvider]] = {
        AuthProvider.GITHUB: GitHubAuthService,
        AuthProvider.AZURE: AzureAuthService,
        AuthProvider.GOOGLE: GoogleAuthService,
        AuthProvider.AUTH0: Auth0AuthService,
    }
    if provider not in services:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    return services[provider]()


def _get_oauth2_config(provider: AuthProvider) -> dict:
    """Get OAuth2 configuration for a provider (no openid scope)."""
    settings = get_settings()

    configs = {
        AuthProvider.AZURE: {
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "redirect_uri": settings.azure_oauth2_redirect_uri,
            "scope": settings.azure_oauth2_scopes,
            "authorization_url": settings.azure_authorization_url,
            "token_url": settings.azure_token_url,
        },
        AuthProvider.GOOGLE: {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_oauth2_redirect_uri,
            "scope": settings.google_oauth2_scopes,
            "authorization_url": settings.google_authorization_url,
            "token_url": settings.google_token_url,
        },
        AuthProvider.AUTH0: {
            "client_id": settings.auth0_client_id,
            "client_secret": settings.auth0_client_secret,
            "redirect_uri": settings.auth0_oauth2_redirect_uri,
            "scope": settings.auth0_oauth2_scopes,
            "authorization_url": settings.auth0_authorization_url,
            "token_url": settings.auth0_token_url,
        },
    }

    if provider not in configs:
        raise HTTPException(status_code=400, detail=f"OAuth2 config not available for: {provider}")
    return configs[provider]


def _build_oauth2_auth_url(provider: AuthProvider, state: str) -> str:
    """Build OAuth2 authorization URL for Azure/Google."""
    config = _get_oauth2_config(provider)

    params = {
        "client_id": config["client_id"],
        "response_type": "code",
        "redirect_uri": config["redirect_uri"],
        "scope": config["scope"],
        "state": state,
    }

    if provider == AuthProvider.AZURE:
        params["response_mode"] = "query"

    return f"{config['authorization_url']}?{urlencode(params)}"


async def _exchange_oauth2_code(provider: AuthProvider, code: str) -> dict[str, Any]:
    """Exchange authorization code for tokens (OAuth2 flow)."""
    config = _get_oauth2_config(provider)
    settings = get_settings()

    proxy = None
    if not settings.disable_proxy:
        proxy = settings.https_proxy or settings.http_proxy

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
    }

    if provider == AuthProvider.AZURE:
        data["scope"] = config["scope"]

    async with get_http_client(proxy=proxy) as client:
        resp = await client.post(config["token_url"], data=data)
        return cast(dict[str, Any], resp.json())


async def _get_user_data(provider: AuthProvider, service: BaseAuthProvider, access_token: str) -> dict[str, Any]:
    """Get user data from provider."""
    if provider == AuthProvider.GITHUB:
        return cast(dict[str, Any], await service.get_user_with_orgs(access_token))  # type: ignore[attr-defined]
    return cast(dict[str, Any], await service.get_user_info(access_token))


@router.get("/providers")
async def list_providers() -> dict[str, Any]:
    """List available authentication providers and their capabilities."""
    settings = get_settings()

    return {
        "default_provider": settings.auth_provider.value,
        "providers": {
            "github": {"oauth2": True, "oidc": False, "id_token": False, "refresh_token": False},
            "azure": {"oauth2": True, "oidc": True, "id_token": True, "refresh_token": True},
            "google": {"oauth2": True, "oidc": True, "id_token": True, "refresh_token": True},
            "auth0": {"oauth2": True, "oidc": True, "id_token": True, "refresh_token": True},
        },
        "endpoints": {
            "oauth2": "/api/v1/auth/oauth2/{provider}/login",
            "oidc": "/api/v1/auth/oidc/{provider}/login",
            "provider_specific": "/api/v1/auth/{provider}/login",
            "logout": "/api/v1/auth/logout",
        },
    }


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> dict[str, Any]:
    """
    Logout user by invalidating the session associated with the bearer token.

    Works with any provider (GitHub, Azure, Google).
    """
    access_token = credentials.credentials
    request_info = get_request_info(request)

    ended_sessions = SessionService.end_sessions_by_token(db, access_token)

    if ended_sessions:
        for session in ended_sessions:
            logger.info(f"Logout: user={session.username}, provider={session.provider}")
            log_logout(db, session.provider, session.user_id, session.username, request_info)
        return {
            "status": "success",
            "message": "Successfully logged out",
            "sessions_ended": len(ended_sessions),
            "details": [
                {
                    "session_id": s.id,
                    "provider": s.provider,
                    "username": s.username,
                    "login_time": s.login_time.isoformat() if s.login_time else None,
                    "logout_time": s.logout_time.isoformat() if s.logout_time else None,
                }
                for s in ended_sessions
            ],
        }

    logger.warning(f"Logout attempted with unknown token from {request_info.get('ip_address')}")
    return {"status": "no_session", "message": "No active session found", "sessions_ended": 0}


@router.get("/oauth2/{provider}/login")
async def oauth2_login(
    provider: AuthProvider,
    logger: Logger = Depends(get_logger),
) -> RedirectResponse:
    """
    Start OAuth2 flow (without openid scope).

    Returns only access_token - no id_token, no refresh_token.
    """
    state = secrets.token_hex(16)

    if provider == AuthProvider.GITHUB:
        service = GitHubAuthService()
        auth_url = service.get_authorization_url(state=state)
    else:
        auth_url = _build_oauth2_auth_url(provider, state)

    _state_map[state] = {"provider": provider.value, "mode": "oauth2"}
    logger.info(f"OAuth2 login initiated: {provider.value}")

    return RedirectResponse(url=auth_url)


@router.get("/oauth2/callback")
async def oauth2_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> dict[str, Any]:
    """
    OAuth2 callback - returns access_token only.

    Demonstrates pure OAuth2 (no id_token, no refresh_token).
    """
    state_data = _state_map.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state")

    provider = AuthProvider(state_data["provider"])
    request_info = get_request_info(request)

    try:
        service: BaseAuthProvider
        if provider == AuthProvider.GITHUB:
            service = GitHubAuthService()
            token_response = await service.exchange_code_for_token(code, state=state)
        else:
            token_response = await _exchange_oauth2_code(provider, code)
            service = _get_service(provider)

        if "error" in token_response:
            log_auth_failure(
                db, provider.value, token_response.get("error_description", "Token exchange failed"), request_info
            )
            raise OAuth2CallbackError(message=f"{provider.value} token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            raise OAuth2CallbackError(message="No access token received")

        user_data = await _get_user_data(provider, service, access_token)

        role_service = get_role_service()
        roles = role_service.get_user_roles(provider.value, user_data)
        unified_user = UnifiedUser.from_provider(provider, user_data, roles, [])

        create_session_and_log(db, provider.value, unified_user, token_response, request_info, roles)

        logger.info(f"OAuth2 auth successful: {unified_user.username or unified_user.email}")

        return {
            "access_token": access_token,
            "token_type": token_response.get("token_type", "Bearer"),
            "user": unified_user.model_dump(),
            "id_token": None,
            "refresh_token": None,
            "expires_in": token_response.get("expires_in"),
            "_info": {"protocol": "oauth2", "provider": provider.value},
        }

    except OAuth2CallbackError:
        raise
    except Exception as e:
        logger.error("OAuth2 callback error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/oidc/{provider}/login")
async def oidc_login(
    provider: AuthProvider,
    logger: Logger = Depends(get_logger),
) -> RedirectResponse:
    """
    Start OIDC flow (with openid scope).

    Returns access_token + id_token + refresh_token.
    """
    if provider == AuthProvider.GITHUB:
        raise HTTPException(
            status_code=400,
            detail="GitHub does NOT support OIDC. Use /api/v1/auth/oauth2/github/login",
        )

    service = _get_service(provider)
    state = secrets.token_hex(16)
    _state_map[state] = {"provider": provider.value, "mode": "oidc"}

    auth_url = service.get_authorization_url(state=state)
    logger.info(f"OIDC login initiated: {provider.value}")

    return RedirectResponse(url=auth_url)


@router.get("/oidc/callback", response_model=AuthResponse)
async def oidc_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> AuthResponse:
    """
    OIDC callback - returns access_token + id_token + refresh_token.

    User info extracted from id_token claims (no API call needed).
    """
    state_data = _state_map.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state")

    provider = AuthProvider(state_data["provider"])
    request_info = get_request_info(request)

    if provider == AuthProvider.GITHUB:
        raise HTTPException(status_code=400, detail="GitHub does not support OIDC")

    try:
        service = _get_service(provider)
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            log_auth_failure(
                db, provider.value, token_response.get("error_description", "Token exchange failed"), request_info
            )
            raise OAuth2CallbackError(message=f"{provider.value} token exchange failed")

        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        refresh_token = token_response.get("refresh_token")

        if not id_token:
            raise OAuth2CallbackError(message="No id_token - OIDC requires openid scope")

        if not access_token:
            raise OAuth2CallbackError(message="No access_token received")

        user_data = await service.get_user_from_token(token_response)  # type: ignore[attr-defined]

        role_service = get_role_service()
        roles = role_service.get_user_roles(provider.value, user_data)
        unified_user = UnifiedUser.from_provider(provider, user_data, roles, [])

        create_session_and_log(db, provider.value, unified_user, token_response, request_info, roles)

        logger.info(f"OIDC auth successful: {unified_user.username or unified_user.email}")

        return AuthResponse(
            access_token=access_token,
            token_type=token_response.get("token_type", "Bearer"),
            user=unified_user,
            id_token=id_token,
            refresh_token=refresh_token,
            expires_in=token_response.get("expires_in"),
        )

    except OAuth2CallbackError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("OIDC callback error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
