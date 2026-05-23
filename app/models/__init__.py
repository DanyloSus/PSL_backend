"""SQLAlchemy ORM model registry.

Import every model module here so Alembic autogenerate sees them via Base.metadata.
"""

from app.core.db import Base

__all__ = ["Base"]
