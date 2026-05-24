from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.core.dependencies import ActivityServiceDep, CurrentUser, UserServiceDep
from app.schemas.activity import ActivityHistoryEntry
from app.schemas.auth import UserPublic
from app.schemas.user import UserStatOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)


@router.get("/me/stats", response_model=list[UserStatOut])
async def get_my_stats(current: CurrentUser, service: UserServiceDep) -> list[UserStatOut]:
    return await service.get_stats(current.id)


@router.get("/me/activity-history", response_model=list[ActivityHistoryEntry])
async def get_my_activity_history(
    current: CurrentUser,
    service: ActivityServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = None,
) -> list[ActivityHistoryEntry]:
    return await service.get_history(current.id, limit=limit, before=before)
