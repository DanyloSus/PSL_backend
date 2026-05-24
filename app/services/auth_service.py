from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.exceptions import (
    EmailTakenError,
    InvalidCredentialsError,
    InvalidRefreshError,
    MissingRefreshError,
    UsernameTakenError,
)
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.services import user_service


@dataclass(slots=True)
class IssuedTokens:
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    csrf_token: str
    user: User


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)

    async def register(self, payload: RegisterRequest, response: Response) -> AuthResponse:
        email = payload.email.lower().strip()
        if await self.users.get_by_email(email):
            raise EmailTakenError
        if await self.users.get_by_username(payload.username):
            raise UsernameTakenError

        user = await self.users.create(
            email=email,
            username=payload.username,
            password_hash=hash_password(payload.password),
        )
        await user_service.initialize_user_stats(self.session, user.id)
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        self._set_cookies(response, tokens)
        return AuthResponse(user=UserPublic.model_validate(user))

    async def login(self, payload: LoginRequest, response: Response) -> AuthResponse:
        user = await self.users.get_by_email(payload.email)
        if (
            user is None
            or not user.is_active
            or not verify_password(payload.password, user.password_hash)
        ):
            raise InvalidCredentialsError
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        self._set_cookies(response, tokens)
        return AuthResponse(user=UserPublic.model_validate(user))

    async def refresh(self, refresh_token_plain: str | None, response: Response) -> AuthResponse:
        if not refresh_token_plain:
            raise MissingRefreshError
        token = await self.refresh_tokens.get_active_by_hash(
            hash_refresh_token(refresh_token_plain)
        )
        if token is None:
            clear_auth_cookies(response)
            raise InvalidRefreshError
        user = await self.users.get_by_id(token.user_id)
        if user is None or not user.is_active:
            clear_auth_cookies(response)
            raise InvalidRefreshError
        await self.refresh_tokens.revoke(token)
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        self._set_cookies(response, tokens)
        return AuthResponse(user=UserPublic.model_validate(user))

    async def logout(self, refresh_token_plain: str | None, response: Response) -> None:
        if refresh_token_plain:
            token = await self.refresh_tokens.get_active_by_hash(
                hash_refresh_token(refresh_token_plain)
            )
            if token is not None:
                await self.refresh_tokens.revoke(token)
        await self.session.commit()
        clear_auth_cookies(response)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        await self.refresh_tokens.revoke_all_for_user(user_id)
        await self.session.commit()

    async def _issue_tokens(self, user: User) -> IssuedTokens:
        access, access_exp = create_access_token(user.id, user.role.value)
        refresh_plain, refresh_digest, refresh_exp = generate_refresh_token()
        await self.refresh_tokens.create(
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

    @staticmethod
    def _set_cookies(response: Response, tokens: IssuedTokens) -> None:
        set_auth_cookies(
            response,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            csrf_token=tokens.csrf_token,
        )
