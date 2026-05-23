from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    session.add(token)
    await session.flush()
    return token


async def get_active_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def revoke(session: AsyncSession, token: RefreshToken) -> None:
    token.revoked_at = datetime.now(UTC)
    await session.flush()


async def revoke_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    now = datetime.now(UTC)
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
