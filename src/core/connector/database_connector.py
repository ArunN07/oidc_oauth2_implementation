from functools import lru_cache
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.exceptions.exceptions import DatabaseConnectionError
from src.core.settings.app import get_settings


@lru_cache(maxsize=10)
def get_engine(database_url: Optional[str] = None) -> Engine:
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


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """
    Create a session factory for the given engine.

    Parameters
    ----------
    engine : Engine, optional
        SQLAlchemy engine. Creates default if not provided.

    Returns
    -------
    sessionmaker
        Session factory.
    """
    if engine is None:
        engine = get_engine()

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Yields
    ------
    Session
        Database session.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection(engine: Optional[Engine] = None) -> bool:
    """
    Check if database connection is working.

    Parameters
    ----------
    engine : Engine, optional
        SQLAlchemy engine to test.

    Returns
    -------
    bool
        True if connection is successful.

    Raises
    ------
    DatabaseConnectionError
        If connection fails.
    """
    if engine is None:
        engine = get_engine()

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        raise DatabaseConnectionError(message="Failed to connect to database", detail=str(e))
