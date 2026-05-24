from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi_limiter.depends import RateLimiter

from app.core.dependencies import AuthServiceDep, CurrentUser
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])

_RATE_LIMIT = [Depends(RateLimiter(times=10, seconds=60))]


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_RATE_LIMIT,
)
async def register(
    payload: RegisterRequest,
    service: AuthServiceDep,
    response: Response,
) -> AuthResponse:
    return await service.register(payload, response)


@router.post("/login", response_model=AuthResponse, dependencies=_RATE_LIMIT)
async def login(
    payload: LoginRequest,
    service: AuthServiceDep,
    response: Response,
) -> AuthResponse:
    return await service.login(payload, response)


@router.post("/refresh", response_model=AuthResponse, dependencies=_RATE_LIMIT)
async def refresh(
    service: AuthServiceDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AuthResponse:
    return await service.refresh(refresh_token, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    service: AuthServiceDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    await service.logout(refresh_token, response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserPublic)
async def me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)
