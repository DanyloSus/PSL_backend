from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stat import Stat
from app.models.user_stat import UserStat


async def list_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[UserStat]:
    result = await session.execute(select(UserStat).where(UserStat.user_id == user_id))
    return list(result.scalars().all())


async def list_for_user_with_stat(
    session: AsyncSession, user_id: uuid.UUID
) -> list[tuple[UserStat, Stat]]:
    result = await session.execute(
        select(UserStat, Stat)
        .join(Stat, Stat.id == UserStat.stat_id)
        .where(UserStat.user_id == user_id)
        .order_by(Stat.display_name)
    )
    return [(us, s) for us, s in result.all()]


async def get_for_update(
    session: AsyncSession, user_id: uuid.UUID, stat_id: uuid.UUID
) -> UserStat | None:
    result = await session.execute(
        select(UserStat)
        .where(UserStat.user_id == user_id, UserStat.stat_id == stat_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def create_for_user(
    session: AsyncSession, user_id: uuid.UUID, stat_ids: list[uuid.UUID]
) -> list[UserStat]:
    rows = [UserStat(user_id=user_id, stat_id=sid) for sid in stat_ids]
    session.add_all(rows)
    await session.flush()
    return rows
