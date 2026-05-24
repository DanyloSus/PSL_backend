from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, SessionDep
from app.repositories import user_stat_repo
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
