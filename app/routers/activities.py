from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from app.core.dependencies import ActivityServiceDep, CurrentUser
from app.schemas.activity import (
    ActivityTemplateOut,
    LogActivityRequest,
    LogActivityResponse,
)

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityTemplateOut])
async def list_activities(
    service: ActivityServiceDep,
    _: CurrentUser,
) -> list[ActivityTemplateOut]:
    return await service.list_templates()


@router.post(
    "/log",
    response_model=LogActivityResponse,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def log_activity(
    payload: LogActivityRequest,
    current: CurrentUser,
    service: ActivityServiceDep,
) -> LogActivityResponse:
    return await service.log_activity(current, payload)
