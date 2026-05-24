from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    *,
    email: str,
    username: str,
    password_hash: str,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        email=email.lower(),
        username=username,
        password_hash=password_hash,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user
