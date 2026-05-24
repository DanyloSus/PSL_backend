from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import ActivityTemplate


async def list_enabled(session: AsyncSession) -> list[ActivityTemplate]:
    result = await session.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.is_enabled.is_(True))
        .options(selectinload(ActivityTemplate.effects))
        .order_by(ActivityTemplate.title)
    )
    return list(result.scalars().all())


async def get_with_effects(
    session: AsyncSession, template_id: uuid.UUID
) -> ActivityTemplate | None:
    result = await session.execute(
        select(ActivityTemplate)
        .where(ActivityTemplate.id == template_id)
        .options(selectinload(ActivityTemplate.effects))
    )
    return result.scalar_one_or_none()
