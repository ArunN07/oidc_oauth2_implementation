"""
Database connector - Redirects to FastAPI utilities.

This module is kept for backward compatibility.
The actual database utilities are now in src/fastapi/utilities/.

See Also
--------
src.fastapi.utilities.database : Actual database connector.
"""

# Re-export from new location for backward compatibility
from src.fastapi.utilities.database import get_db, get_engine

__all__ = ["get_db", "get_engine"]
