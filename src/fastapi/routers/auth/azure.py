"""Azure AD OIDC authentication router."""

import secrets
from logging import Logger

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.azure_service import AzureAuthService
from src.fastapi.services.auth.role_service import get_role_service

router = APIRouter(prefix="/azure", tags=["Azure"])


def get_azure_service() -> AzureAuthService:
    return AzureAuthService()


@router.get("/login")
async def azure_login(
    redirect: bool = Query(False),
    service: AzureAuthService = Depends(get_azure_service),
    logger: Logger = Depends(get_logger),
):
    """Initiate Azure AD OIDC login flow."""
    state = secrets.token_hex(16)
    auth_url = service.get_authorization_url(state=state)
    logger.info(f"Azure login: state={state[:8]}...")

    if redirect:
        return RedirectResponse(url=auth_url)
    return {"authorization_url": auth_url, "state": state}


@router.get("/callback", response_model=AuthResponse)
async def azure_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    service: AzureAuthService = Depends(get_azure_service),
    logger: Logger = Depends(get_logger),
):
    """Handle Azure AD OIDC callback."""
    try:
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            raise OAuth2CallbackError(message="Azure token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            raise OAuth2CallbackError(message="No access token")

        user_data = await service.get_user_from_token(token_response)

        role_service = get_role_service()
        roles = role_service.get_user_roles("azure", user_data)
        groups = role_service.get_user_groups("azure", user_data)

        unified_user = UnifiedUser.from_azure(user_data, roles, groups)
        logger.info(f"Azure auth: {unified_user.username}, roles={roles}")

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
        logger.error(f"Azure callback error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
