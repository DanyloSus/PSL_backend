from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stat import Stat


class StatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Stat]:
        result = await self.session.execute(select(Stat).order_by(Stat.display_name))
        return list(result.scalars().all())
