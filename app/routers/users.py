from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, UserServiceDep
from app.schemas.auth import UserPublic
from app.schemas.user import UserStatOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)


@router.get("/me/stats", response_model=list[UserStatOut])
async def get_my_stats(current: CurrentUser, service: UserServiceDep) -> list[UserStatOut]:
    return await service.get_stats(current.id)
