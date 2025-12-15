"""
FastAPI Application Entry Point.

This module creates and configures the FastAPI application with OAuth2/OIDC
authentication support, middleware, exception handlers, and API routes.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn

# Import services to trigger provider registration with factory
# pylint: disable=unused-import
import src.fastapi.services  # noqa: F401
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import AuthError, BaseAppException, ProviderNotSupportedError
from src.core.settings.app import get_settings
from src.fastapi.api import api_router

# pylint: enable=unused-import


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Creates log directories and logs application startup information.

    Parameters
    ----------
    _app : FastAPI
        The FastAPI application instance (unused but required by FastAPI).

    Yields
    ------
    None
        Yields control to the application.
    """
    settings = get_settings()
    logger = get_logger()

    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger.info("Starting %s v%s", settings.title, settings.version)
    logger.info("Environment: %s", settings.app_env.value)
    logger.info("Default Auth Provider: %s", settings.auth_provider.value)
    logger.info("Debug Mode: %s", settings.debug)

    db_url = settings.get_database_url()
    db_display = db_url.split("@")[-1] if "@" in db_url else db_url
    logger.info("Database: %s", db_display)

    yield

    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.
    """
    settings = get_settings()

    # Enhanced description with auth instructions
    description = f"""{settings.description}

## 🔐 Authentication

This API demonstrates OAuth2 and OIDC authentication flows.

### How to Authenticate:

1. **Login via OAuth2/OIDC:**
   - [GitHub Login](/api/v1/auth/github/login) → Returns `access_token`
   - [Azure Login](/api/v1/auth/azure/login) → Returns `access_token` + `id_token`
   - [Google Login](/api/v1/auth/google/login) → Returns `access_token` + `id_token`

2. **Use the token in Swagger:**
   - Click the **Authorize** 🔓 button above
   - Enter: `Bearer <your_access_token>`
   - Click **Authorize**

### OAuth2 vs OIDC Comparison Endpoints (Generic):
- **OAuth2 Flow:** `/api/v1/auth/oauth2/{{provider}}/login` → Returns `access_token` only
- **OIDC Flow:** `/api/v1/auth/oidc/{{provider}}/login` → Returns `access_token` + `id_token`
- **Providers:** `/api/v1/auth/providers` → List available providers and their capabilities
"""

    app = FastAPI(
        title=settings.title,
        description=description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add Bearer token security scheme to OpenAPI
    def custom_openapi() -> dict:  # type: ignore[type-arg]
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.title,
            version=settings.version,
            description=description,
            routes=app.routes,
        )
        # Add Bearer token security scheme for Swagger UI "Authorize" button
        # scheme_name="BearerAuth" in HTTPBearer must match this key
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}

        openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the access_token from OAuth2/OIDC login response",
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(_request: Request, exc: BaseAppException) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(AuthError)
    async def auth_exception_handler(_request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(ProviderNotSupportedError)
    async def provider_exception_handler(_request: Request, exc: ProviderNotSupportedError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "supported_providers": exc.supported_providers,
            },
        )

    # Include routers
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()

    PORT = 8001

    print(f"Starting server on http://127.0.0.1:{PORT}")
    print(f"Swagger UI: http://127.0.0.1:{PORT}/docs")
    print(f"OAuth2 Test: http://127.0.0.1:{PORT}/api/v1/auth/demo/test/comparison")

    uvicorn.run(
        "src.fastapi.main:app",
        host="127.0.0.1",
        port=PORT,
        reload=settings.debug,
    )
