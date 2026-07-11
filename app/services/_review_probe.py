from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class ReviewProbeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user(self, user_id: str) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="not found")
        return user
