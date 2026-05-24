from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import ActivityTemplate


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_enabled(self) -> list[ActivityTemplate]:
        result = await self.session.execute(
            select(ActivityTemplate)
            .where(ActivityTemplate.is_enabled.is_(True))
            .options(selectinload(ActivityTemplate.effects))
            .order_by(ActivityTemplate.title)
        )
        return list(result.scalars().all())

    async def list_by_ids(self, ids: list[uuid.UUID]) -> list[ActivityTemplate]:
        result = await self.session.execute(
            select(ActivityTemplate)
            .where(ActivityTemplate.id.in_(ids))
            .options(selectinload(ActivityTemplate.effects))
            .order_by(ActivityTemplate.title)
        )
        return list(result.scalars().all())

    async def get_with_effects(self, template_id: uuid.UUID) -> ActivityTemplate | None:
        result = await self.session.execute(
            select(ActivityTemplate)
            .where(ActivityTemplate.id == template_id)
            .options(selectinload(ActivityTemplate.effects))
        )
        return result.scalar_one_or_none()
