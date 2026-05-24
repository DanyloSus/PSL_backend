from __future__ import annotations

from httpx import AsyncClient


async def test_user_role_default_is_user(auth_client: AsyncClient) -> None:
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["role"] == "USER"


async def test_admin_promotion_yields_admin_role(admin_client: AsyncClient) -> None:
    r = await admin_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"
