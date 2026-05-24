from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import csrf_tokens_match, decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CSRF_HEADER = "X-CSRF-Token"
_STATE_CHANGING = {"POST", "PUT", "PATCH", "DELETE"}


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


async def get_current_user(
    users: UserRepositoryDep,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    try:
        payload = decode_access_token(access_token)
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="access token expired"
        ) from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid access token"
        ) from err

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="wrong token type")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token subject"
        ) from err

    user = await users.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not active")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


async def verify_csrf(
    request: Request,
    csrf_token: Annotated[str | None, Cookie()] = None,
    x_csrf_token: Annotated[str | None, Header(alias=CSRF_HEADER)] = None,
) -> None:
    if request.method not in _STATE_CHANGING:
        return
    if request.url.path.endswith(("/auth/login", "/auth/register", "/auth/refresh")):
        return
    if not csrf_tokens_match(csrf_token or "", x_csrf_token or ""):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF check failed")


CSRFGuard = Annotated[None, Depends(verify_csrf)]
