from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(
        self,
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
        self.session.add(user)
        await self.session.flush()
        return user
