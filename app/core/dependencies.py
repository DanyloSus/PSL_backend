from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import csrf_tokens_match, decode_access_token
from app.models.user import User, UserRole
from app.repositories import user_repo

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CSRF_HEADER = "X-CSRF-Token"
_STATE_CHANGING = {"POST", "PUT", "PATCH", "DELETE"}


async def get_current_user(
    session: SessionDep,
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

    user = await user_repo.get_by_id(session, user_id)
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
    # Allow login/register/refresh without CSRF (no session yet).
    if request.url.path.endswith(("/auth/login", "/auth/register", "/auth/refresh")):
        return
    if not csrf_tokens_match(csrf_token or "", x_csrf_token or ""):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF check failed")


CSRFGuard = Annotated[None, Depends(verify_csrf)]
