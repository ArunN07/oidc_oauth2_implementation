from functools import lru_cache
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

from src.core.exceptions.exceptions import DatabaseConnectionError
from src.core.models.database_models import AuthenticationLog, UserSession  # noqa: F401
from src.core.settings.app import get_settings


def _create_tables(engine: Engine) -> None:
    """
    Creates all tables defined in the database models if they don't exist.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine instance.
    """
    SQLModel.metadata.create_all(engine)


@lru_cache(maxsize=10)
def get_engine(database_url: str | None = None) -> Engine:
    """
    Create or retrieve a cached SQLAlchemy engine.

    Parameters
    ----------
    database_url : str, optional
        Database URL. Uses settings if not provided.

    Returns
    -------
    Engine
        SQLAlchemy engine instance.
    """
    settings = get_settings()
    url = database_url or settings.get_database_url()

    return create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
    )


@lru_cache(maxsize=10)
def _ensure_tables_initialized(engine: Engine) -> bool:
    """
    Ensures database tables are initialized once per engine.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine instance.

    Returns
    -------
    bool
        True if initialization succeeded.
    """
    try:
        _create_tables(engine)
        return True
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(
            message="Failed to initialize database tables",
            detail=str(e)
        )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Yields
    ------
    Session
        Database session.
    """
    engine = get_engine()
    _ensure_tables_initialized(engine)

    with Session(engine) as session:
        yield session


