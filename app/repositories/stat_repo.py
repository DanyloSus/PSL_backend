from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stat import Stat


async def list_all(session: AsyncSession) -> list[Stat]:
    result = await session.execute(select(Stat).order_by(Stat.display_name))
    return list(result.scalars().all())
