import secrets
from logging import Logger
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from src.core.auth.factory import get_auth_provider
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import OAuth2CallbackError, ProviderNotSupportedError
from src.core.settings.app import get_settings
from src.fastapi.models.auth.common_models import AuthResponse, UnifiedUser
from src.fastapi.services.auth.role_service import get_role_service

router = APIRouter(tags=["Generic Auth"])

# State -> Provider mapping for callback
_state_provider_map: dict = {}


@router.get("/providers")
async def list_providers(
    logger: Logger = Depends(get_logger),
):
    """List all available authentication providers."""
    settings = get_settings()

    return {
        "default_provider": settings.auth_provider.value,
        "available_providers": ["github", "azure", "google"],
        "generic_endpoints": {
            "login": "/api/v1/auth/login",
            "login_with_override": "/api/v1/auth/login?provider=azure",
            "callback": "/api/v1/auth/callback",
        },
        "provider_endpoints": {
            "github": "/api/v1/auth/github/login",
            "azure": "/api/v1/auth/azure/login",
            "google": "/api/v1/auth/google/login",
        },
    }


@router.get("/login")
async def generic_login(
    provider: Optional[str] = Query(None, description="Override AUTH_PROVIDER"),
    redirect: bool = Query(False, description="Redirect to provider"),
    logger: Logger = Depends(get_logger),
):
    """
    Generic login - uses AUTH_PROVIDER from .env or override with ?provider= param.

    Uses provider-specific redirect URIs configured in .env, so no portal changes needed.

    Examples:
        /login                     -> Uses AUTH_PROVIDER from .env
        /login?provider=github     -> Uses GitHub
        /login?provider=azure      -> Uses Azure
        /login?redirect=true       -> Redirects to provider login page
    """
    settings = get_settings()
    provider_name = provider or settings.auth_provider.value

    logger.info(f"Generic login with provider: {provider_name}")

    try:
        auth_service = get_auth_provider(provider_name)
        state = secrets.token_hex(16)
        auth_url = auth_service.get_authorization_url(state=state)

        # Store state -> provider mapping (for generic callback if used)
        _state_provider_map[state] = provider_name

        if redirect:
            return RedirectResponse(url=auth_url)

        return {
            "provider": provider_name,
            "authorization_url": auth_url,
            "state": state,
            "note": f"Callback will go to provider-specific endpoint: /auth/{provider_name}/callback",
        }

    except ProviderNotSupportedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider_name}' not supported. Use: github, azure, google",
        )


@router.get("/callback", response_model=AuthResponse)
async def generic_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    provider: Optional[str] = Query(None, description="Override provider detection"),
    logger: Logger = Depends(get_logger),
):
    """
    Generic callback - auto-detects provider from state or uses override.

    The provider is determined by:
    1. ?provider= query param (if provided)
    2. State mapping from /login call
    3. AUTH_PROVIDER from .env (fallback)
    """
    # Determine provider
    provider_name = provider or _state_provider_map.pop(state, None)
    if not provider_name:
        settings = get_settings()
        provider_name = settings.auth_provider.value
        logger.warning(f"State not found, using default: {provider_name}")

    logger.info(f"Generic callback for provider: {provider_name}")

    try:
        auth_service = get_auth_provider(provider_name)

        # Exchange code for token (pass state for PKCE code_verifier)
        token_response = await auth_service.exchange_code_for_token(code, state=state)

        if "error" in token_response:
            raise OAuth2CallbackError(
                message=f"{provider_name} token exchange failed",
                detail=token_response.get("error_description", token_response.get("error")),
            )

        access_token = token_response.get("access_token")
        if not access_token:
            raise OAuth2CallbackError(message="No access token received")

        # Get user info based on provider capabilities
        if hasattr(auth_service, "get_user_from_token"):
            user_data = await auth_service.get_user_from_token(token_response)
        elif hasattr(auth_service, "get_user_with_orgs"):
            user_data = await auth_service.get_user_with_orgs(access_token)
        else:
            user_data = await auth_service.get_user_info(access_token)

        # Get roles and groups
        role_service = get_role_service()
        roles = role_service.get_user_roles(provider_name, user_data)
        groups = role_service.get_user_groups(provider_name, user_data)

        # Create unified user
        unified_user = UnifiedUser.from_provider(provider_name, user_data, roles, groups)

        logger.info(f"Auth successful: {unified_user.username or unified_user.email}, roles: {roles}")

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
    except ProviderNotSupportedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider_name}' not supported",
        )
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Authentication failed: {str(e)}")
