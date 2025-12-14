"""
Database connector for FastAPI OAuth2/OIDC demo.

This module provides database connection utilities using SQLModel (SQLAlchemy).
It creates and manages database connections, initializes tables, and provides
a FastAPI dependency for database sessions.

Functions
---------
get_engine
    Get or create a cached SQLAlchemy engine.
get_db
    FastAPI dependency that yields database sessions.

Examples
--------
Using the database dependency in a FastAPI endpoint:

>>> from fastapi import Depends
>>> from sqlmodel import Session
>>> from src.fastapi.utilities.database import get_db
>>>
>>> @router.get("/sessions")
>>> async def list_sessions(db: Session = Depends(get_db)):
...     return db.query(UserSession).all()
"""

from functools import lru_cache
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

from src.core.exceptions.exceptions import DatabaseConnectionError
from src.core.settings.app import get_settings

# Import models to ensure they're registered with SQLModel metadata
from src.fastapi.models.database.session_models import (  # noqa: F401
    AuthenticationLog,
    UserSession,
)


def _create_tables(engine: Engine) -> None:
    """
    Create all database tables if they don't exist.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine instance.

    Notes
    -----
    This uses SQLModel's metadata.create_all() which only creates
    tables that don't already exist. Safe to call multiple times.
    """
    SQLModel.metadata.create_all(engine)


@lru_cache(maxsize=1)
def get_engine(database_url: str | None = None) -> Engine:
    """
    Get or create a cached SQLAlchemy engine.

    This function uses LRU caching to ensure only one engine instance
    is created per database URL.

    Parameters
    ----------
    database_url : str | None, optional
        Database connection URL. If not provided, uses BACKEND_DB_URL from
        environment or falls back to settings.

    Returns
    -------
    Engine
        SQLAlchemy engine instance.

    Notes
    -----
    Supported database URLs:
    - PostgreSQL: postgresql://user:password@host:port/dbname
    - SQLite: sqlite:///./database.db

    Environment variable: BACKEND_DB_URL
    """
    import os

    # Priority: parameter > BACKEND_DB_URL env > settings
    url = database_url or os.getenv("BACKEND_DB_URL") or get_settings().get_database_url()

    # SQLite doesn't support connection pooling options
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
        )

    # PostgreSQL and other databases support pooling
    return create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def _ensure_tables_initialized(engine_id: int) -> bool:
    """
    Ensure database tables are initialized (called once per engine).

    Parameters
    ----------
    engine_id : int
        The id() of the engine (used as cache key).

    Returns
    -------
    bool
        True if initialization succeeded.

    Raises
    ------
    DatabaseConnectionError
        If table initialization fails.
    """
    engine = get_engine()
    try:
        _create_tables(engine)
        return True
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(
            message="Failed to initialize database tables", detail=str(e)
        )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Yields a database session that is automatically closed after use.
    Tables are initialized on first call.

    Yields
    ------
    Session
        SQLModel database session.

    Examples
    --------
    >>> @router.get("/data")
    >>> async def get_data(db: Session = Depends(get_db)):
    ...     return db.query(MyModel).all()
    """
    engine = get_engine()
    _ensure_tables_initialized(id(engine))

    with Session(engine) as session:
        yield session

