from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
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
        template_id: uuid.UUID | None = None,
        from_: datetime | None = None,
        to: datetime | None = None,
    ) -> list[ActivityLog]:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .options(
                selectinload(ActivityLog.template),
                selectinload(ActivityLog.effects_applied).selectinload(ActivityLogEffect.stat),
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        if before is not None:
            stmt = stmt.where(ActivityLog.created_at < before)
        if template_id is not None:
            stmt = stmt.where(ActivityLog.template_id == template_id)
        if from_ is not None:
            stmt = stmt.where(ActivityLog.created_at >= from_)
        if to is not None:
            stmt = stmt.where(ActivityLog.created_at <= to)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(
        self,
        user_id: uuid.UUID,
        *,
        template_id: uuid.UUID | None = None,
        from_: datetime | None = None,
        to: datetime | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(ActivityLog).where(ActivityLog.user_id == user_id)
        if template_id is not None:
            stmt = stmt.where(ActivityLog.template_id == template_id)
        if from_ is not None:
            stmt = stmt.where(ActivityLog.created_at >= from_)
        if to is not None:
            stmt = stmt.where(ActivityLog.created_at <= to)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_owned(self, user_id: uuid.UUID, log_id: uuid.UUID) -> ActivityLog | None:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.id == log_id, ActivityLog.user_id == user_id)
            .options(selectinload(ActivityLog.effects_applied))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, log: ActivityLog) -> None:
        await self.session.delete(log)
        await self.session.flush()
