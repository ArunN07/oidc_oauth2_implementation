"""GitHub OAuth2 authentication router."""

import secrets
from logging import Logger

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.github_service import GitHubAuthService
from src.fastapi.services.auth.role_service import get_role_service

router = APIRouter(prefix="/github", tags=["GitHub"])


def get_github_service() -> GitHubAuthService:
    return GitHubAuthService()


@router.get("/login")
async def github_login(
    redirect: bool = Query(False),
    service: GitHubAuthService = Depends(get_github_service),
    logger: Logger = Depends(get_logger),
):
    """Initiate GitHub OAuth2 login flow."""
    state = secrets.token_hex(16)
    auth_url = service.get_authorization_url(state=state)
    logger.info(f"GitHub login: state={state[:8]}...")

    if redirect:
        return RedirectResponse(url=auth_url)
    return {"authorization_url": auth_url, "state": state}


@router.get("/callback", response_model=AuthResponse)
async def github_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    service: GitHubAuthService = Depends(get_github_service),
    logger: Logger = Depends(get_logger),
):
    """Handle GitHub OAuth2 callback."""
    try:
        token_response = await service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            raise OAuth2CallbackError(message="GitHub token exchange failed")

        access_token = token_response.get("access_token")
        if not access_token:
            raise OAuth2CallbackError(message="No access token")

        user_data = await service.get_user_with_orgs(access_token)

        role_service = get_role_service()
        roles = role_service.get_user_roles("github", user_data)
        groups = role_service.get_user_groups("github", user_data)

        unified_user = UnifiedUser.from_github(user_data, roles, groups)
        logger.info(f"GitHub auth: {unified_user.username}, roles={roles}")

        return AuthResponse(
            access_token=access_token,
            token_type=token_response.get("token_type", "bearer"),
            user=unified_user,
            id_token=None,  # GitHub doesn't support OIDC
            refresh_token=None,
            expires_in=None,
        )

    except OAuth2CallbackError:
        raise
    except Exception as e:
        logger.error(f"GitHub callback error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
