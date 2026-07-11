from __future__ import annotations

import json
import uuid
from datetime import datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    LogNotFoundError,
    QuantityOutOfRangeError,
    TemplateDisabledError,
    TemplateNotFoundError,
)
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
    ActivityHistoryPage,
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

        if template.input_type is ActivityInputType.BINARY:
            effective_qty = 1
        else:
            if not template.min_quantity <= payload.quantity <= template.max_quantity:
                raise QuantityOutOfRangeError(
                    f"quantity must be between {template.min_quantity} and {template.max_quantity}"
                )
            effective_qty = payload.quantity

        stat_ids = [eff.stat_id for eff in template.effects]
        stat_rows = await self.session.execute(select(Stat).where(Stat.id.in_(stat_ids)))
        stats_by_id = {s.id: s for s in stat_rows.scalars().all()}

        applied_out: list[AppliedEffect] = []
        total_applied = 0
        effects_for_log: list[tuple[uuid.UUID, int]] = []

        for effect in template.effects:
            raw_delta = effect.xp_change * effective_qty
            user_stat = await self.user_stats.get_for_update(user.id, effect.stat_id)
            if user_stat is None:
                user_stat = UserStat(user_id=user.id, stat_id=effect.stat_id, xp=0, level=1)
                self.session.add(user_stat)
                await self.session.flush()

            old_xp = user_stat.xp
            new_xp = max(0, old_xp + raw_delta)
            actual_delta = new_xp - old_xp
            user_stat.xp = new_xp

            old_level = user_stat.level
            computed_level = LevelingService.level_from_xp(new_xp)
            new_level = max(old_level, computed_level)
            user_stat.level = new_level

            total_applied += actual_delta
            effects_for_log.append((effect.stat_id, actual_delta))

            stat_progress = LevelingService.progress(new_xp)
            applied_out.append(
                AppliedEffect(
                    stat=StatOut.model_validate(stats_by_id[effect.stat_id]),
                    xp_applied=actual_delta,
                    xp=new_xp,
                    level=new_level,
                    leveled_up=new_level > old_level,
                    previous_level=old_level,
                    levels_gained=new_level - old_level,
                    xp_into_level=stat_progress.xp_into_level,
                    xp_for_next=stat_progress.xp_for_next,
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

        global_progress = LevelingService.progress(new_global_xp)
        return LogActivityResponse(
            log_id=log.id,
            total_xp_applied=total_applied,
            applied=applied_out,
            global_xp=user.global_xp,
            global_level=user.global_level,
            global_leveled_up=new_global_level > old_global_level,
            previous_global_level=old_global_level,
            global_levels_gained=new_global_level - old_global_level,
            xp_into_level=global_progress.xp_into_level,
            xp_for_next=global_progress.xp_for_next,
        )

    async def get_history(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        before: datetime | None = None,
        template_id: uuid.UUID | None = None,
        from_: datetime | None = None,
        to: datetime | None = None,
    ) -> ActivityHistoryPage:
        rows = await self.logs.list_for_user(
            user_id,
            limit=limit + 1,
            before=before,
            template_id=template_id,
            from_=from_,
            to=to,
        )
        has_more = len(rows) > limit
        page_rows = rows[:limit]
        total = await self.logs.count_for_user(user_id, template_id=template_id, from_=from_, to=to)
        items = [
            ActivityHistoryEntry(
                id=log.id,
                activity_template_id=log.template_id,
                title=log.template.title,
                description=log.template.description,
                input_type=log.template.input_type,
                quantity=log.quantity,
                total_xp_applied=log.total_xp_applied,
                created_at=log.created_at,
                effects=[
                    ActivityHistoryEffect(
                        stat_id=effect.stat_id,
                        xp_applied=effect.xp_applied,
                        key=effect.stat.key,
                        display_name=effect.stat.display_name,
                        icon=effect.stat.icon,
                    )
                    for effect in log.effects_applied
                ],
            )
            for log in page_rows
        ]
        next_before = page_rows[-1].created_at if has_more and page_rows else None
        return ActivityHistoryPage(
            items=items,
            total=total,
            has_more=has_more,
            next_before=next_before,
        )

    async def delete_log(self, user: User, log_id: uuid.UUID) -> None:
        log = await self.logs.get_owned(user.id, log_id)
        if log is None:
            raise LogNotFoundError

        for effect in log.effects_applied:
            user_stat = await self.user_stats.get_for_update(user.id, effect.stat_id)
            if user_stat is None:
                continue
            user_stat.xp = max(0, user_stat.xp - effect.xp_applied)
            recomputed = LevelingService.level_from_xp(user_stat.xp)
            user_stat.level = max(user_stat.level, recomputed)

        user.global_xp = max(0, user.global_xp - log.total_xp_applied)
        user.global_level = max(user.global_level, LevelingService.level_from_xp(user.global_xp))

        await self.logs.delete(log)
        await self.session.commit()

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
            min_quantity=template.min_quantity,
            max_quantity=template.max_quantity,
            effects=[ActivityEffectOut.model_validate(e) for e in template.effects],
        )
