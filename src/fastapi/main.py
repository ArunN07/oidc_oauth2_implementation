import os
from contextlib import asynccontextmanager

import uvicorn

# Import services to trigger provider registration with factory
import src.fastapi.services  # noqa: F401
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from src.core.configuration.logger_dependency import get_logger
from src.core.exceptions.exceptions import AuthError, BaseAppException, ProviderNotSupportedError
from src.core.settings.app import get_settings
from src.fastapi.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Creates log directories and logs application startup information.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.

    Yields
    ------
    None
        Yields control to the application.
    """
    # Startup
    settings = get_settings()
    logger = get_logger()

    # Ensure logs directory exists
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger.info(f"Starting {settings.title} v{settings.version}")
    logger.info(f"Environment: {settings.app_env.value}")
    logger.info(f"Default Auth Provider: {settings.auth_provider.value}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Database: {settings.get_database_url().split('@')[-1] if '@' in settings.get_database_url() else settings.get_database_url()}")

    yield

    # Shutdown
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
    def custom_openapi():
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

    app.openapi = custom_openapi

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
    async def app_exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(AuthError)
    async def auth_exception_handler(request: Request, exc: AuthError):
        return JSONResponse(
            status_code=401,
            content={
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(ProviderNotSupportedError)
    async def provider_exception_handler(request: Request, exc: ProviderNotSupportedError):
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

    # Try port 8001 first, fallback to 8002 if blocked
    port = 8001

    print(f"Starting server on http://127.0.0.1:{port}")
    print(f"Swagger UI: http://127.0.0.1:{port}/docs")
    print(f"OAuth2 Test: http://127.0.0.1:{port}/api/v1/auth/demo/test/comparison")

    uvicorn.run(
        "src.fastapi.main:app",
        host="127.0.0.1",
        port=port,
        reload=settings.debug,
    )
