from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import stat_repo, user_stat_repo


async def initialize_user_stats(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Create one UserStat row per seeded Stat for the new user."""
    stats = await stat_repo.list_all(session)
    if not stats:
        return
    await user_stat_repo.create_for_user(session, user_id, [s.id for s in stats])
