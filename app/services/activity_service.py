from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import ActivityInputType, ActivityTemplate
from app.models.stat import Stat
from app.models.user import User
from app.models.user_stat import UserStat
from app.repositories import activity_log_repo, activity_repo, user_stat_repo
from app.services.leveling import level_from_xp

TEMPLATES_CACHE_KEY = "activities:templates"
TEMPLATES_CACHE_TTL = 300  # 5 minutes


class ActivityError(Exception):
    pass


class TemplateNotFoundError(ActivityError):
    pass


class TemplateDisabledError(ActivityError):
    pass


@dataclass(slots=True)
class AppliedEffectResult:
    stat: Stat
    xp_applied: int
    new_xp: int
    new_level: int
    leveled_up: bool


@dataclass(slots=True)
class LogActivityResult:
    log_id: uuid.UUID
    total_xp_applied: int
    applied: list[AppliedEffectResult]
    user: User
    global_leveled_up: bool


async def list_templates(session: AsyncSession, redis: Redis) -> list[ActivityTemplate]:
    cached = await redis.get(TEMPLATES_CACHE_KEY)
    if cached:
        ids = json.loads(cached)
        result = await session.execute(
            select(ActivityTemplate)
            .where(ActivityTemplate.id.in_(ids))
            .options(selectinload(ActivityTemplate.effects))
            .order_by(ActivityTemplate.title)
        )
        rows = list(result.scalars().all())
        if len(rows) == len(ids):
            return rows
    templates = await activity_repo.list_enabled(session)
    await redis.set(
        TEMPLATES_CACHE_KEY,
        json.dumps([str(t.id) for t in templates]),
        ex=TEMPLATES_CACHE_TTL,
    )
    return templates


async def invalidate_templates_cache(redis: Redis) -> None:
    await redis.delete(TEMPLATES_CACHE_KEY)


async def log_activity(
    session: AsyncSession,
    *,
    user: User,
    template_id: uuid.UUID,
    quantity: int,
) -> LogActivityResult:
    template = await activity_repo.get_with_effects(session, template_id)
    if template is None:
        raise TemplateNotFoundError
    if not template.is_enabled:
        raise TemplateDisabledError

    effective_qty = 1 if template.input_type is ActivityInputType.BINARY else max(1, quantity)

    stat_ids = [eff.stat_id for eff in template.effects]
    stat_rows = await session.execute(select(Stat).where(Stat.id.in_(stat_ids)))
    stats_by_id = {s.id: s for s in stat_rows.scalars().all()}

    applied: list[AppliedEffectResult] = []
    total_applied = 0
    effects_for_log: list[tuple[uuid.UUID, int]] = []

    for effect in template.effects:
        raw_delta = effect.xp_change * effective_qty
        us = await user_stat_repo.get_for_update(session, user.id, effect.stat_id)
        if us is None:
            us = UserStat(user_id=user.id, stat_id=effect.stat_id, xp=0, level=1)
            session.add(us)
            await session.flush()

        old_xp = us.xp
        new_xp = max(0, old_xp + raw_delta)
        actual_delta = new_xp - old_xp
        us.xp = new_xp

        old_level = us.level
        computed_level = level_from_xp(new_xp)
        new_level = max(old_level, computed_level)
        leveled_up = new_level > old_level
        us.level = new_level

        total_applied += actual_delta
        effects_for_log.append((effect.stat_id, actual_delta))

        applied.append(
            AppliedEffectResult(
                stat=stats_by_id[effect.stat_id],
                xp_applied=actual_delta,
                new_xp=new_xp,
                new_level=new_level,
                leveled_up=leveled_up,
            )
        )

    old_global_xp = user.global_xp
    new_global_xp = max(0, old_global_xp + total_applied)
    user.global_xp = new_global_xp
    old_global_level = user.global_level
    new_global_level = max(old_global_level, level_from_xp(new_global_xp))
    user.global_level = new_global_level
    global_leveled_up = new_global_level > old_global_level

    log = await activity_log_repo.create(
        session,
        user_id=user.id,
        template_id=template.id,
        quantity=effective_qty,
        total_xp_applied=total_applied,
        effects_applied=effects_for_log,
    )

    await session.commit()

    return LogActivityResult(
        log_id=log.id,
        total_xp_applied=total_applied,
        applied=applied,
        user=user,
        global_leveled_up=global_leveled_up,
    )
