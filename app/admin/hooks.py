"""Listen for ORM mutations on activity templates/effects and invalidate Redis cache."""

from __future__ import annotations

import asyncio

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.redis import get_redis_client
from app.models.activity import ActivityEffect, ActivityTemplate
from app.services.activity_service import TEMPLATES_CACHE_KEY

_pending: set[asyncio.Task[None]] = set()


async def _do_invalidate() -> None:
    await get_redis_client().delete(TEMPLATES_CACHE_KEY)


def _schedule_cache_invalidation() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    task = loop.create_task(_do_invalidate())
    _pending.add(task)
    task.add_done_callback(_pending.discard)


def _on_change(_mapper: object, _connection: object, _target: object) -> None:
    _schedule_cache_invalidation()


def register_cache_hooks() -> None:
    for model in (ActivityTemplate, ActivityEffect):
        event.listen(model, "after_insert", _on_change)
        event.listen(model, "after_update", _on_change)
        event.listen(model, "after_delete", _on_change)
    # Safety net: also flush after each Session commit that touched these models.

    def after_commit(session: Session) -> None:
        for obj in session.new | session.dirty | session.deleted:
            if isinstance(obj, ActivityTemplate | ActivityEffect):
                _schedule_cache_invalidation()
                return

    event.listen(Session, "after_commit", after_commit)
