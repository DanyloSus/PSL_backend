from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import ActivityServiceDep, CurrentUser, UserServiceDep
from app.schemas.activity import ActivityHistoryPage
from app.schemas.auth import UserPublic
from app.schemas.user import UserStatOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)


@router.post("/me/complete-onboarding", response_model=UserPublic)
async def complete_onboarding(current: CurrentUser, service: UserServiceDep) -> UserPublic:
    return await service.complete_onboarding(current)


@router.get("/me/stats", response_model=list[UserStatOut])
async def get_my_stats(current: CurrentUser, service: UserServiceDep) -> list[UserStatOut]:
    return await service.get_stats(current.id)


@router.get("/me/activity-history", response_model=ActivityHistoryPage)
async def get_my_activity_history(
    current: CurrentUser,
    service: ActivityServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = None,
    template_id: uuid.UUID | None = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
) -> ActivityHistoryPage:
    return await service.get_history(
        current.id,
        limit=limit,
        before=before,
        template_id=template_id,
        from_=from_,
        to=to,
    )


@router.delete("/me/activity-history/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_activity_log(
    log_id: uuid.UUID,
    current: CurrentUser,
    service: ActivityServiceDep,
) -> None:
    await service.delete_log(current, log_id)
