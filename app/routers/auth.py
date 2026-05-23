from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi_limiter.depends import RateLimiter

from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


_RATE_LIMIT = [Depends(RateLimiter(times=10, seconds=60))]


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_RATE_LIMIT,
)
async def register(
    payload: RegisterRequest, session: SessionDep, response: Response
) -> AuthResponse:
    try:
        tokens = await auth_service.register(
            session,
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
    except auth_service.EmailTakenError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from err
    except auth_service.UsernameTakenError as err:
        raise HTTPException(status.HTTP_409_CONFLICT, "username already taken") from err

    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        csrf_token=tokens.csrf_token,
    )
    return AuthResponse(user=UserPublic.model_validate(tokens.user))


@router.post("/login", response_model=AuthResponse, dependencies=_RATE_LIMIT)
async def login(payload: LoginRequest, session: SessionDep, response: Response) -> AuthResponse:
    try:
        tokens = await auth_service.login(session, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials") from err

    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        csrf_token=tokens.csrf_token,
    )
    return AuthResponse(user=UserPublic.model_validate(tokens.user))


@router.post("/refresh", response_model=AuthResponse, dependencies=_RATE_LIMIT)
async def refresh(
    session: SessionDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing refresh token")
    try:
        tokens = await auth_service.refresh(session, refresh_token_plain=refresh_token)
    except auth_service.InvalidRefreshError as err:
        clear_auth_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token") from err

    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        csrf_token=tokens.csrf_token,
    )
    return AuthResponse(user=UserPublic.model_validate(tokens.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session: SessionDep,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    await auth_service.logout(session, refresh_token_plain=refresh_token)
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserPublic)
async def me(current: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current)
