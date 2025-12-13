"""
Database initialization script.

Creates tables for session tracking and authentication logging using SQLModel.
Run this script to set up the database schema.

Usage:
    poetry run python scripts/init_db.py
"""

from sqlmodel import SQLModel, create_engine

from src.core.settings.app import get_settings


def init_database():
    """
    Initialize database tables using SQLModel.

    Creates all tables defined in the database models if they don't exist.
    """
    # Import models to register them with SQLModel
    from src.core.models.database_models import AuthenticationLog, UserSession  # noqa: F401

    settings = get_settings()
    database_url = settings.get_database_url()

    print(f"Connecting to database: {database_url}")

    engine = create_engine(database_url, echo=True)

    print("Creating tables...")
    SQLModel.metadata.create_all(engine)

    print("\n" + "=" * 50)
    print("Database initialized successfully!")
    print("=" * 50)
    print("\nCreated tables:")
    print("  - user_sessions      (OAuth2/OIDC session tracking)")
    print("  - authentication_logs (Authentication attempt logging)")
    print("\nYou can now run the application with:")
    print("  poetry run uvicorn src.fastapi.main:app --host 127.0.0.1 --port 8001 --reload")


if __name__ == "__main__":
    init_database()
