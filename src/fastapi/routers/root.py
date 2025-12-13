"""Root and utility endpoints."""

from fastapi import APIRouter
from src.core.settings.app import get_settings

router = APIRouter(tags=["🏠 Root"])


@router.get("/")
async def root():
    """Root endpoint - application information."""
    settings = get_settings()
    return {
        "name": settings.title,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "providers": "/providers",
            "auth": f"{settings.api_prefix}/auth",
        },
    }


@router.get("/health")
async def health():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.app_env.value,
        "auth_provider": settings.auth_provider.value,
    }


@router.get("/providers")
async def providers():
    """List available authentication providers and their endpoints."""
    settings = get_settings()
    return {
        "active_provider": settings.auth_provider.value,
        "available_providers": ["github", "azure", "google"],
        "protocol_support": {
            "github": {"oauth2": True, "oidc": False},
            "azure": {"oauth2": True, "oidc": True},
            "google": {"oauth2": True, "oidc": True},
        },
        "endpoints": {
            "github": {
                "login": f"{settings.api_prefix}/auth/github/login",
                "callback": f"{settings.api_prefix}/auth/github/callback",
            },
            "azure": {
                "login": f"{settings.api_prefix}/auth/azure/login",
                "callback": f"{settings.api_prefix}/auth/azure/callback",
            },
            "google": {
                "login": f"{settings.api_prefix}/auth/google/login",
                "callback": f"{settings.api_prefix}/auth/google/callback",
            },
        },
        "demo_endpoints": {
            "oauth2_test": {
                "github": f"{settings.api_prefix}/auth/demo/test/oauth2/github/login",
                "azure": f"{settings.api_prefix}/auth/demo/test/oauth2/azure/login",
                "google": f"{settings.api_prefix}/auth/demo/test/oauth2/google/login",
            },
            "oidc_test": {
                "github": "❌ Not supported",
                "azure": f"{settings.api_prefix}/auth/demo/test/oidc/azure/login",
                "google": f"{settings.api_prefix}/auth/demo/test/oidc/google/login",
            },
            "comparison": f"{settings.api_prefix}/auth/demo/test/comparison",
        },
    }
