"""Demo endpoints for OAuth2 vs OIDC comparison."""

import secrets
from logging import Logger
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.core.configuration.logger_dependency import get_logger
from src.core.connector.database_connector import get_db
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.core.settings.app import get_settings
from src.fastapi.models.auth.common_models import UnifiedUser
from src.fastapi.services.auth.azure_service import AzureAuthService
from src.fastapi.services.auth.github_service import GitHubAuthService
from src.fastapi.services.auth.google_service import GoogleAuthService
from src.fastapi.services.auth.role_service import get_role_service

router = APIRouter(prefix="/demo", tags=["Demo"])

_state_provider_map: dict[str, dict[str, str]] = {}


def _get_request_info(request: Request) -> dict[str, str | None]:
    """Extract request metadata."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("/oauth2/{provider}/login")
async def oauth2_login(
    provider: str,
    redirect: bool = Query(True),
    logger: Logger = Depends(get_logger),
):
    """Start OAuth2 flow (without openid scope - no id_token)."""
    provider = provider.lower()
    settings = get_settings()
    state = secrets.token_hex(16)

    match provider:
        case "github":
            service = GitHubAuthService()
            auth_url = service.get_authorization_url(state=state)
        case "azure":
            # OAuth2-only: no openid scope = no id_token
            params = {
                "client_id": settings.azure_client_id,
                "response_type": "code",
                "redirect_uri": settings.azure_redirect_uri,
                "scope": "https://graph.microsoft.com/User.Read",
                "state": state,
                "response_mode": "query",
            }
            auth_url = f"{settings.azure_authorization_url}?{urlencode(params)}"
        case "google":
            # OAuth2-only: no openid scope = no id_token
            params = {
                "client_id": settings.google_client_id,
                "response_type": "code",
                "redirect_uri": settings.google_redirect_uri,
                "scope": (
                    "https://www.googleapis.com/auth/userinfo.profile "
                    "https://www.googleapis.com/auth/userinfo.email"
                ),
                "state": state,
                "access_type": "offline",
            }
            auth_url = f"{settings.google_authorization_url}?{urlencode(params)}"
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    _state_provider_map[state] = {"provider": provider, "mode": "oauth2"}
    logger.info(f"OAuth2 login: {provider}")

    if redirect:
        return RedirectResponse(url=auth_url)
    return {"authorization_url": auth_url, "state": state}


@router.get("/oauth2/callback")
async def oauth2_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
):
    """OAuth2 callback - exchanges code for access_token only."""
    state_data = _state_provider_map.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state")

    provider = state_data["provider"]
    settings = get_settings()

    try:
        match provider:
            case "github":
                service = GitHubAuthService()
                token_response = await service.exchange_code_for_token(code, state=state)
            case "azure":
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.azure_client_id,
                    "client_secret": settings.azure_client_secret,
                    "redirect_uri": settings.azure_redirect_uri,
                    "scope": "https://graph.microsoft.com/User.Read",
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(settings.azure_token_url, data=data)
                    token_response = resp.json()
                service = AzureAuthService()
            case "google":
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(settings.google_token_url, data=data)
                    token_response = resp.json()
                service = GoogleAuthService()
            case _:
                raise HTTPException(status_code=400, detail="Unknown provider")

        if "error" in token_response:
            raise OAuth2CallbackError(message=f"{provider} token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            raise OAuth2CallbackError(message="No access token")

        user_data = (
            await service.get_user_with_orgs(access_token)
            if provider == "github"
            else await service.get_user_info(access_token)
        )

        role_service = get_role_service()
        roles = role_service.get_user_roles(provider, user_data)
        unified_user = UnifiedUser.from_provider(provider, user_data, roles, [])

        return {
            "protocol": "oauth2",
            "provider": provider,
            "tokens": {
                "access_token": f"{access_token[:20]}...",
                "id_token": None,
                "refresh_token": token_response.get("refresh_token"),
            },
            "user_info_source": "API call (OAuth2 requires this)",
            "user": unified_user.model_dump(),
        }

    except OAuth2CallbackError:
        raise
    except Exception as e:
        logger.error(f"OAuth2 callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oidc/{provider}/login")
async def oidc_login(
    provider: str,
    redirect: bool = Query(True),
    logger: Logger = Depends(get_logger),
):
    """Start OIDC flow (with openid scope - gets id_token)."""
    provider = provider.lower()

    match provider:
        case "github":
            return {"error": "GitHub does NOT support OIDC", "use_instead": "/demo/oauth2/github/login"}
        case "azure":
            service = AzureAuthService()
        case "google":
            service = GoogleAuthService()
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    state = secrets.token_hex(16)
    _state_provider_map[state] = {"provider": provider, "mode": "oidc"}

    auth_url = service.get_authorization_url(state=state)
    logger.info(f"OIDC login: {provider}")

    if redirect:
        return RedirectResponse(url=auth_url)
    return {"authorization_url": auth_url, "state": state}


@router.get("/oidc/callback")
async def oidc_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    logger: Logger = Depends(get_logger),
):
    """OIDC callback - exchanges code for access_token + id_token + refresh_token."""
    state_data = _state_provider_map.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid state")

    provider = state_data["provider"]

    try:
        match provider:
            case "azure":
                service = AzureAuthService()
            case "google":
                service = GoogleAuthService()
            case _:
                raise HTTPException(status_code=400, detail=f"OIDC not supported: {provider}")

        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            raise OAuth2CallbackError(message=f"{provider} token exchange failed")

        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        refresh_token = token_response.get("refresh_token")

        if not id_token:
            raise OAuth2CallbackError(message="No id_token - OIDC requires openid scope")

        id_token_claims = service.decode_id_token(id_token)
        user_data = await service.get_user_from_token(token_response)

        role_service = get_role_service()
        roles = role_service.get_user_roles(provider, user_data)
        unified_user = UnifiedUser.from_provider(provider, user_data, roles, [])

        return {
            "protocol": "oidc",
            "provider": provider,
            "tokens": {
                "access_token": f"{access_token[:20]}..." if access_token else None,
                "id_token": f"{id_token[:20]}..." if id_token else None,
                "refresh_token": f"{refresh_token[:20]}..." if refresh_token else None,
                "expires_in": token_response.get("expires_in"),
            },
            "id_token_claims": {
                "iss": id_token_claims.get("iss"),
                "sub": id_token_claims.get("sub"),
                "email": id_token_claims.get("email"),
                "name": id_token_claims.get("name"),
            },
            "user_info_source": "id_token claims (no API call needed!)",
            "user": unified_user.model_dump(),
        }

    except OAuth2CallbackError:
        raise
    except Exception as e:
        logger.error(f"OIDC callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comparison")
async def comparison():
    """Compare OAuth2 vs OIDC capabilities across providers."""
    return {
        "providers": {
            "github": {"oauth2": True, "oidc": False, "id_token": False, "refresh_token": False},
            "azure": {"oauth2": True, "oidc": True, "id_token": True, "refresh_token": True},
            "google": {"oauth2": True, "oidc": True, "id_token": True, "refresh_token": True},
        },
        "endpoints": {"oauth2": "/demo/oauth2/{provider}/login", "oidc": "/demo/oidc/{provider}/login"},
    }
