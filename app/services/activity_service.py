from __future__ import annotations

import json
import uuid
from datetime import datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TemplateDisabledError, TemplateNotFoundError
from app.models.activity import ActivityInputType
from app.models.stat import Stat
from app.models.user import User
from app.models.user_stat import UserStat
from app.repositories.activity_log_repo import ActivityLogRepository
from app.repositories.activity_repo import ActivityRepository
from app.repositories.user_stat_repo import UserStatRepository
from app.schemas.activity import (
    ActivityEffectOut,
    ActivityHistoryEffect,
    ActivityHistoryEntry,
    ActivityTemplateOut,
    AppliedEffect,
    LogActivityRequest,
    LogActivityResponse,
)
from app.schemas.user import StatOut
from app.services.leveling import LevelingService

TEMPLATES_CACHE_KEY = "activities:templates"
TEMPLATES_CACHE_TTL = 300  # 5 minutes


class ActivityService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis
        self.templates = ActivityRepository(session)
        self.logs = ActivityLogRepository(session)
        self.user_stats = UserStatRepository(session)

    async def list_templates(self) -> list[ActivityTemplateOut]:
        cached = await self.redis.get(TEMPLATES_CACHE_KEY)
        if cached:
            ids = json.loads(cached)
            rows = await self.templates.list_by_ids(ids)
            if len(rows) == len(ids):
                return [self._template_out(t) for t in rows]

        templates = await self.templates.list_enabled()
        await self.redis.set(
            TEMPLATES_CACHE_KEY,
            json.dumps([str(t.id) for t in templates]),
            ex=TEMPLATES_CACHE_TTL,
        )
        return [self._template_out(t) for t in templates]

    async def invalidate_templates_cache(self) -> None:
        await self.redis.delete(TEMPLATES_CACHE_KEY)

    async def log_activity(
        self,
        user: User,
        payload: LogActivityRequest,
    ) -> LogActivityResponse:
        template = await self.templates.get_with_effects(payload.activity_template_id)
        if template is None:
            raise TemplateNotFoundError
        if not template.is_enabled:
            raise TemplateDisabledError

        effective_qty = (
            1 if template.input_type is ActivityInputType.BINARY else max(1, payload.quantity)
        )

        stat_ids = [eff.stat_id for eff in template.effects]
        stat_rows = await self.session.execute(select(Stat).where(Stat.id.in_(stat_ids)))
        stats_by_id = {s.id: s for s in stat_rows.scalars().all()}

        applied_out: list[AppliedEffect] = []
        total_applied = 0
        effects_for_log: list[tuple[uuid.UUID, int]] = []

        for effect in template.effects:
            raw_delta = effect.xp_change * effective_qty
            us = await self.user_stats.get_for_update(user.id, effect.stat_id)
            if us is None:
                us = UserStat(user_id=user.id, stat_id=effect.stat_id, xp=0, level=1)
                self.session.add(us)
                await self.session.flush()

            old_xp = us.xp
            new_xp = max(0, old_xp + raw_delta)
            actual_delta = new_xp - old_xp
            us.xp = new_xp

            old_level = us.level
            computed_level = LevelingService.level_from_xp(new_xp)
            new_level = max(old_level, computed_level)
            us.level = new_level

            total_applied += actual_delta
            effects_for_log.append((effect.stat_id, actual_delta))

            applied_out.append(
                AppliedEffect(
                    stat=StatOut.model_validate(stats_by_id[effect.stat_id]),
                    xp_applied=actual_delta,
                    xp=new_xp,
                    level=new_level,
                    leveled_up=new_level > old_level,
                )
            )

        old_global_xp = user.global_xp
        new_global_xp = max(0, old_global_xp + total_applied)
        user.global_xp = new_global_xp
        old_global_level = user.global_level
        new_global_level = max(old_global_level, LevelingService.level_from_xp(new_global_xp))
        user.global_level = new_global_level

        log = await self.logs.create(
            user_id=user.id,
            template_id=template.id,
            quantity=effective_qty,
            total_xp_applied=total_applied,
            effects_applied=effects_for_log,
        )

        await self.session.commit()

        return LogActivityResponse(
            log_id=log.id,
            total_xp_applied=total_applied,
            applied=applied_out,
            global_xp=user.global_xp,
            global_level=user.global_level,
            global_leveled_up=new_global_level > old_global_level,
        )

    async def get_history(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        before: datetime | None = None,
    ) -> list[ActivityHistoryEntry]:
        logs = await self.logs.list_for_user(user_id, limit=limit, before=before)
        return [
            ActivityHistoryEntry(
                id=log.id,
                activity_template_id=log.template_id,
                quantity=log.quantity,
                total_xp_applied=log.total_xp_applied,
                created_at=log.created_at,
                effects=[
                    ActivityHistoryEffect(stat_id=e.stat_id, xp_applied=e.xp_applied)
                    for e in log.effects_applied
                ],
            )
            for log in logs
        ]

    @staticmethod
    def _template_out(template: object) -> ActivityTemplateOut:
        # template is ActivityTemplate; declared as object to keep the static helper
        # decoupled from the model module already imported in this file.
        from app.models.activity import ActivityTemplate

        assert isinstance(template, ActivityTemplate)
        return ActivityTemplateOut(
            id=template.id,
            title=template.title,
            description=template.description,
            input_type=template.input_type,
            is_enabled=template.is_enabled,
            effects=[ActivityEffectOut.model_validate(e) for e in template.effects],
        )
