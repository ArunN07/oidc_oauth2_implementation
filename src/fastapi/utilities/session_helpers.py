"""
Session helper utilities for authentication.

This module provides reusable helper functions for session management
and authentication logging across all auth routers.

Functions
---------
create_session_and_log : Create session and log successful authentication.
log_auth_failure : Log failed authentication attempt.
log_logout : Log successful logout event.
get_request_info : Extract request metadata for logging.
"""

from fastapi import Request
from sqlmodel import Session

from src.fastapi.models.auth.common_models import UnifiedUser
from src.fastapi.services.database.session_service import SessionService


def get_request_info(request: Request) -> dict[str, str]:
    """
    Extract request metadata for logging.

    Parameters
    ----------
    request : Request
        FastAPI request object.

    Returns
    -------
    dict[str, str]
        Dictionary with ip_address and user_agent.
    """
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def create_session_and_log(
    db: Session,
    provider: str,
    unified_user: UnifiedUser,
    token_response: dict,
    request_info: dict,
    roles: list[str],
) -> None:
    """
    Create session and log successful authentication.

    Parameters
    ----------
    db : Session
        SQLModel database session.
    provider : str
        Provider name ('github', 'azure', 'google').
    unified_user : UnifiedUser
        Unified user model with user details.
    token_response : dict
        Token response from provider.
    request_info : dict
        Request metadata (ip_address, user_agent).
    roles : list[str]
        User roles.
    """
    session_user_data = {
        "id": unified_user.id,
        "provider": provider,
        "username": unified_user.username,
        "email": unified_user.email,
        "roles": roles,
    }
    SessionService.create_session(db, session_user_data, token_response, request_info)
    SessionService.log_authentication(
        db=db,
        provider=provider,
        success=True,
        user_id=unified_user.id,
        username=unified_user.username,
        request_info=request_info,
    )


def log_auth_failure(
    db: Session,
    provider: str,
    error_message: str,
    request_info: dict,
) -> None:
    """
    Log failed authentication attempt.

    Parameters
    ----------
    db : Session
        SQLModel database session.
    provider : str
        Provider name ('github', 'azure', 'google').
    error_message : str
        Error message describing the failure.
    request_info : dict
        Request metadata (ip_address, user_agent).
    """
    SessionService.log_authentication(
        db=db,
        provider=provider,
        success=False,
        error_message=error_message,
        request_info=request_info,
    )


def log_logout(
    db: Session,
    provider: str,
    user_id: str | None,
    username: str | None,
    request_info: dict,
) -> None:
    """
    Log successful logout event.

    Parameters
    ----------
    db : Session
        SQLModel database session.
    provider : str
        Provider name ('github', 'azure', 'google').
    user_id : str | None
        User ID if available.
    username : str | None
        Username if available.
    request_info : dict
        Request metadata (ip_address, user_agent).
    """
    SessionService.log_authentication(
        db=db,
        provider=provider,
        success=True,
        user_id=user_id,
        username=username,
        error_message="logout",  # Indicates logout event
        request_info=request_info,
    )

