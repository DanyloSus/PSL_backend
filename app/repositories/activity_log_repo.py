from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import ActivityLog, ActivityLogEffect


class ActivityLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        quantity: int,
        total_xp_applied: int,
        effects_applied: list[tuple[uuid.UUID, int]],
    ) -> ActivityLog:
        log = ActivityLog(
            user_id=user_id,
            template_id=template_id,
            quantity=quantity,
            total_xp_applied=total_xp_applied,
        )
        self.session.add(log)
        await self.session.flush()
        rows = [
            ActivityLogEffect(log_id=log.id, stat_id=stat_id, xp_applied=xp)
            for stat_id, xp in effects_applied
        ]
        self.session.add_all(rows)
        await self.session.flush()
        return log

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        before: datetime | None = None,
    ) -> list[ActivityLog]:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .options(selectinload(ActivityLog.effects_applied))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        if before is not None:
            stmt = stmt.where(ActivityLog.created_at < before)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
