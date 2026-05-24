from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stat_repo import StatRepository
from app.repositories.user_stat_repo import UserStatRepository
from app.schemas.user import StatOut, UserStatOut
from app.services.leveling import LevelingService


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.stats = StatRepository(session)
        self.user_stats = UserStatRepository(session)

    async def initialize_user_stats(self, user_id: uuid.UUID) -> None:
        """Create one UserStat row per seeded Stat for the new user."""
        seeded = await self.stats.list_all()
        if not seeded:
            return
        await self.user_stats.create_for_user(user_id, [stat.id for stat in seeded])

    async def get_stats(self, user_id: uuid.UUID) -> list[UserStatOut]:
        rows = await self.user_stats.list_for_user_with_stat(user_id)
        out: list[UserStatOut] = []
        for user_stat, stat in rows:
            progress = LevelingService.progress(user_stat.xp)
            out.append(
                UserStatOut(
                    stat=StatOut.model_validate(stat),
                    xp=user_stat.xp,
                    level=user_stat.level,
                    xp_into_level=progress.xp_into_level,
                    xp_for_next=progress.xp_for_next,
                )
            )
        return out
