from fastapi import APIRouter
from src.fastapi.routers.auth.auth0 import router as auth0_router
from src.fastapi.routers.auth.azure import router as azure_router
from src.fastapi.routers.auth.generic import router as generic_router
from src.fastapi.routers.auth.github import router as github_router
from src.fastapi.routers.auth.google import router as google_router
from src.fastapi.routers.root import router as root_router

# Main API router
api_router = APIRouter()

# Root endpoints (/, /health, /providers)
api_router.include_router(root_router)

# Auth endpoints - all under /auth prefix
api_router.include_router(generic_router, prefix="/auth")
api_router.include_router(github_router, prefix="/auth")
api_router.include_router(azure_router, prefix="/auth")
api_router.include_router(google_router, prefix="/auth")
api_router.include_router(auth0_router, prefix="/auth")
