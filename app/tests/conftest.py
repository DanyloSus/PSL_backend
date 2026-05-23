from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

_USE_OVERRIDE = bool(os.getenv("TEST_DATABASE_URL")) and bool(os.getenv("TEST_REDIS_URL"))


def _async_db_url_from_container(pg: Any) -> str:
    host = pg.get_container_host_ip()
    port = pg.get_exposed_port(5432)
    return f"postgresql+asyncpg://psl:psl@{host}:{port}/psl"


def _redis_url_from_container(rc: Any) -> str:
    host = rc.get_container_host_ip()
    port = rc.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    if _USE_OVERRIDE:
        yield os.environ["TEST_DATABASE_URL"]
        return
    from testcontainers.postgres import PostgresContainer

    pg = PostgresContainer("postgres:16-alpine", username="psl", password="psl", dbname="psl")
    pg.start()
    try:
        yield _async_db_url_from_container(pg)
    finally:
        pg.stop()


@pytest.fixture(scope="session")
def redis_url(database_url: str) -> Iterator[str]:
    _ = database_url  # ordering: ensure DB url chosen first
    if _USE_OVERRIDE:
        yield os.environ["TEST_REDIS_URL"]
        return
    from testcontainers.redis import RedisContainer

    rc = RedisContainer("redis:7-alpine")
    rc.start()
    try:
        yield _redis_url_from_container(rc)
    finally:
        rc.stop()


@pytest.fixture(scope="session", autouse=True)
def configure_env(database_url: str, redis_url: str) -> Iterator[None]:
    os.environ["DATABASE_URL"] = database_url
    os.environ["REDIS_URL"] = redis_url
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["CSRF_SECRET"] = "test-csrf"
    os.environ["ENV"] = "local"
    os.environ["COOKIE_SECURE"] = "false"
    os.environ["COOKIE_SAMESITE"] = "lax"

    from app.core import config as cfg

    cfg.get_settings.cache_clear()

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")

    yield


@pytest.fixture(autouse=True)
async def clean_user_data() -> AsyncIterator[None]:
    from sqlalchemy import text

    from app.core.db import dispose_engine, get_sessionmaker
    from app.core.redis import close_redis, get_redis_client

    sm = get_sessionmaker()
    async with sm() as session:
        await session.execute(text("TRUNCATE refresh_tokens RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE activity_log_effects RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE activity_logs RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE user_stats RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
        await session.commit()
    # Flush Redis (rate limit state + template cache) between tests.
    with contextlib.suppress(Exception):
        await get_redis_client().flushdb()
    yield
    await dispose_engine()
    await close_redis()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as ac,
        app.router.lifespan_context(app),
    ):
        yield ac


async def _register(
    client: AsyncClient,
    *,
    email: str = "tester@psl.io",
    username: str = "tester",
    password: str = "secret123",
) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert resp.status_code == 201, resp.text
    return {"csrf_token": resp.cookies.get("csrf_token") or ""}


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    info = await _register(client)
    client.headers["X-CSRF-Token"] = info["csrf_token"]
    return client


@pytest.fixture
async def admin_client(client: AsyncClient) -> AsyncClient:
    info = await _register(client, email="admin@psl.io", username="admin", password="adminpass123")
    from sqlalchemy import update

    from app.core.db import get_sessionmaker
    from app.models.user import User, UserRole

    sm = get_sessionmaker()
    async with sm() as session:
        await session.execute(
            update(User).where(User.email == "admin@psl.io").values(role=UserRole.ADMIN)
        )
        await session.commit()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@psl.io", "password": "adminpass123"},
    )
    assert resp.status_code == 200
    client.headers["X-CSRF-Token"] = resp.cookies.get("csrf_token") or info["csrf_token"]
    return client
