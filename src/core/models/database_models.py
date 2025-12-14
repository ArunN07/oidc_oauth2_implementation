"""
Database models - Redirects to FastAPI models.

This module is kept for backward compatibility.
The actual models are now in src/fastapi/models/database/.

See Also
--------
src.fastapi.models.database.session_models : Actual model implementations.
"""

# Re-export from new location for backward compatibility
from src.fastapi.models.database.session_models import (
    AuthenticationLog,
    UserSession,
)

__all__ = ["UserSession", "AuthenticationLog"]
