"""
Session service - Redirects to FastAPI services.

This module is kept for backward compatibility.
The actual service is now in src/fastapi/services/database/.

See Also
--------
src.fastapi.services.database.session_service : Actual service implementation.
"""

# Re-export from new location for backward compatibility
from src.fastapi.services.database.session_service import SessionService

__all__ = ["SessionService"]
