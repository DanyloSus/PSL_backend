"""SQLAlchemy ORM model registry.

Import every model module here so Alembic autogenerate sees them via Base.metadata.
"""

from app.core.db import Base
from app.models.activity import (
    ActivityEffect,
    ActivityInputType,
    ActivityLog,
    ActivityLogEffect,
    ActivityTemplate,
)
from app.models.refresh_token import RefreshToken
from app.models.stat import Stat
from app.models.user import User, UserRole
from app.models.user_stat import UserStat

__all__ = [
    "ActivityEffect",
    "ActivityInputType",
    "ActivityLog",
    "ActivityLogEffect",
    "ActivityTemplate",
    "Base",
    "RefreshToken",
    "Stat",
    "User",
    "UserRole",
    "UserStat",
]
