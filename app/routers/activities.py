from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from redis.asyncio import Redis

from app.core.dependencies import CurrentUser, SessionDep
from app.core.redis import get_redis
from app.schemas.activity import (
    ActivityEffectOut,
    ActivityTemplateOut,
    AppliedEffect,
    LogActivityRequest,
    LogActivityResponse,
)
from app.schemas.user import StatOut
from app.services import activity_service

router = APIRouter(prefix="/activities", tags=["activities"])

RedisDep = Annotated[Redis, Depends(get_redis)]


@router.get("", response_model=list[ActivityTemplateOut])
async def list_activities(
    session: SessionDep,
    redis: RedisDep,
    _: CurrentUser,
) -> list[ActivityTemplateOut]:
    templates = await activity_service.list_templates(session, redis)
    return [
        ActivityTemplateOut(
            id=t.id,
            title=t.title,
            description=t.description,
            input_type=t.input_type,
            is_enabled=t.is_enabled,
            effects=[ActivityEffectOut.model_validate(e) for e in t.effects],
        )
        for t in templates
    ]


@router.post(
    "/log",
    response_model=LogActivityResponse,
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def log_activity(
    payload: LogActivityRequest,
    current: CurrentUser,
    session: SessionDep,
) -> LogActivityResponse:
    try:
        result = await activity_service.log_activity(
            session,
            user=current,
            template_id=payload.activity_template_id,
            quantity=payload.quantity,
        )
    except activity_service.TemplateNotFoundError as err:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "activity not found") from err
    except activity_service.TemplateDisabledError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, "activity disabled") from err

    from app.services.leveling import progress  # local import avoids cycle

    applied_out = []
    for a in result.applied:
        p = progress(a.new_xp)
        applied_out.append(
            AppliedEffect(
                stat=StatOut.model_validate(a.stat),
                xp_applied=a.xp_applied,
                xp=a.new_xp,
                level=a.new_level,
                leveled_up=a.leveled_up,
            )
        )
        _ = p  # progress reserved for future expansion
    return LogActivityResponse(
        log_id=result.log_id,
        total_xp_applied=result.total_xp_applied,
        applied=applied_out,
        global_xp=result.user.global_xp,
        global_level=result.user.global_level,
        global_leveled_up=result.global_leveled_up,
    )
