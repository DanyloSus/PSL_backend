from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stat import Stat
from app.models.user_stat import UserStat


class UserStatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[UserStat]:
        result = await self.session.execute(select(UserStat).where(UserStat.user_id == user_id))
        return list(result.scalars().all())

    async def list_for_user_with_stat(self, user_id: uuid.UUID) -> list[tuple[UserStat, Stat]]:
        result = await self.session.execute(
            select(UserStat, Stat)
            .join(Stat, Stat.id == UserStat.stat_id)
            .where(UserStat.user_id == user_id)
            .order_by(Stat.display_name)
        )
        return [(user_stat, stat) for user_stat, stat in result.all()]

    async def get_for_update(self, user_id: uuid.UUID, stat_id: uuid.UUID) -> UserStat | None:
        result = await self.session.execute(
            select(UserStat)
            .where(UserStat.user_id == user_id, UserStat.stat_id == stat_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def create_for_user(
        self, user_id: uuid.UUID, stat_ids: list[uuid.UUID]
    ) -> list[UserStat]:
        rows = [UserStat(user_id=user_id, stat_id=sid) for sid in stat_ids]
        self.session.add_all(rows)
        await self.session.flush()
        return rows
