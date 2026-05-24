from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories import refresh_token_repo, user_repo


class AuthError(Exception):
    pass


class EmailTakenError(AuthError):
    pass


class UsernameTakenError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshError(AuthError):
    pass


@dataclass(slots=True)
class IssuedTokens:
    access_token: str
    access_expires_at: datetime
    refresh_token: str  # plain (return to client only)
    csrf_token: str
    user: User


async def register(
    session: AsyncSession, *, email: str, username: str, password: str
) -> IssuedTokens:
    email = email.lower().strip()
    if await user_repo.get_by_email(session, email):
        raise EmailTakenError
    if await user_repo.get_by_username(session, username):
        raise UsernameTakenError

    user = await user_repo.create(
        session,
        email=email,
        username=username,
        password_hash=hash_password(password),
    )
    tokens = await _issue_tokens(session, user)
    await session.commit()
    return tokens


async def login(session: AsyncSession, *, email: str, password: str) -> IssuedTokens:
    user = await user_repo.get_by_email(session, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    tokens = await _issue_tokens(session, user)
    await session.commit()
    return tokens


async def refresh(session: AsyncSession, *, refresh_token_plain: str) -> IssuedTokens:
    token = await refresh_token_repo.get_active_by_hash(
        session, hash_refresh_token(refresh_token_plain)
    )
    if token is None:
        raise InvalidRefreshError
    user = await user_repo.get_by_id(session, token.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshError
    # Rotate: revoke old, issue new.
    await refresh_token_repo.revoke(session, token)
    tokens = await _issue_tokens(session, user)
    await session.commit()
    return tokens


async def logout(session: AsyncSession, *, refresh_token_plain: str | None) -> None:
    if refresh_token_plain:
        token = await refresh_token_repo.get_active_by_hash(
            session, hash_refresh_token(refresh_token_plain)
        )
        if token is not None:
            await refresh_token_repo.revoke(session, token)
    await session.commit()


async def logout_all(session: AsyncSession, *, user_id: uuid.UUID) -> None:
    await refresh_token_repo.revoke_all_for_user(session, user_id)
    await session.commit()


async def _issue_tokens(session: AsyncSession, user: User) -> IssuedTokens:
    access, access_exp = create_access_token(user.id, user.role.value)
    refresh_plain, refresh_digest, refresh_exp = generate_refresh_token()
    await refresh_token_repo.create(
        session,
        user_id=user.id,
        token_hash=refresh_digest,
        expires_at=refresh_exp,
    )
    return IssuedTokens(
        access_token=access,
        access_expires_at=access_exp,
        refresh_token=refresh_plain,
        csrf_token=generate_csrf_token(),
        user=user,
    )
