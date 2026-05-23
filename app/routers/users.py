from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, SessionDep
from app.repositories import activity_log_repo, user_stat_repo
from app.schemas.activity import ActivityHistoryEffect, ActivityHistoryEntry
from app.schemas.auth import UserPublic
from app.schemas.user import StatOut, UserStatOut
from app.services.leveling import progress

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)


@router.get("/me/stats", response_model=list[UserStatOut])
async def get_my_stats(current: CurrentUser, session: SessionDep) -> list[UserStatOut]:
    rows = await user_stat_repo.list_for_user_with_stat(session, current.id)
    out: list[UserStatOut] = []
    for us, s in rows:
        p = progress(us.xp)
        out.append(
            UserStatOut(
                stat=StatOut.model_validate(s),
                xp=us.xp,
                level=us.level,
                xp_into_level=p.xp_into_level,
                xp_for_next=p.xp_for_next,
            )
        )
    return out


@router.get("/me/activity-history", response_model=list[ActivityHistoryEntry])
async def get_my_activity_history(
    current: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = None,
) -> list[ActivityHistoryEntry]:
    logs = await activity_log_repo.list_for_user(session, current.id, limit=limit, before=before)
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
