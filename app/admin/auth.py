from __future__ import annotations

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.security import verify_password
from app.models.user import UserRole
from app.repositories import user_repo


class AdminAuth(AuthenticationBackend):
    def __init__(self) -> None:
        super().__init__(secret_key=get_settings().jwt_secret)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = str(form.get("username", "")).strip().lower()
        password = str(form.get("password", ""))
        if not email or not password:
            return False
        sm = get_sessionmaker()
        async with sm() as session:
            user = await user_repo.get_by_email(session, email)
        if user is None or not user.is_active:
            return False
        if user.role is not UserRole.ADMIN:
            return False
        if not verify_password(password, user.password_hash):
            return False
        request.session["admin_user_id"] = str(user.id)
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool | RedirectResponse | Response:
        return "admin_user_id" in request.session
