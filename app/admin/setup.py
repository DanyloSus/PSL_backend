from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin

from app.admin.auth import AdminAuth
from app.admin.hooks import register_cache_hooks
from app.admin.views import ALL_VIEWS
from app.core.db import get_engine


def mount_admin(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=get_engine(),
        authentication_backend=AdminAuth(),
        title="PSL Admin",
    )
    for view in ALL_VIEWS:
        admin.add_view(view)
    register_cache_hooks()
