"""SQLAlchemy ORM model registry.

Import every model module here so Alembic autogenerate sees them via Base.metadata.
"""

from app.core.db import Base
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

__all__ = ["Base", "RefreshToken", "User", "UserRole"]
