from __future__ import annotations

from httpx import AsyncClient


async def test_new_user_starts_un_onboarded(auth_client: AsyncClient) -> None:
    # @trace FR-ONBOARD-1
    r = await auth_client.get("/api/v1/users/me")
    assert r.status_code == 200, r.text
    assert r.json()["onboarding_completed"] is False


async def test_complete_onboarding_sets_flag(auth_client: AsyncClient) -> None:
    # @trace FR-ONBOARD-2 FR-ONBOARD-1
    r = await auth_client.post("/api/v1/users/me/complete-onboarding")
    assert r.status_code == 200, r.text
    assert r.json()["onboarding_completed"] is True

    me = await auth_client.get("/api/v1/auth/me")
    assert me.json()["onboarding_completed"] is True


async def test_complete_onboarding_is_idempotent(auth_client: AsyncClient) -> None:
    # @trace FR-ONBOARD-2
    first = await auth_client.post("/api/v1/users/me/complete-onboarding")
    assert first.status_code == 200
    second = await auth_client.post("/api/v1/users/me/complete-onboarding")
    assert second.status_code == 200
    assert second.json()["onboarding_completed"] is True


async def test_complete_onboarding_requires_auth(client: AsyncClient) -> None:
    # @trace NFR-ONBOARD-1
    client.cookies.set("csrf_token", "abc")
    client.headers["X-CSRF-Token"] = "abc"
    r = await client.post("/api/v1/users/me/complete-onboarding")
    assert r.status_code == 401, r.text


async def test_complete_onboarding_requires_csrf(auth_client: AsyncClient) -> None:
    # @trace NFR-ONBOARD-1
    del auth_client.headers["X-CSRF-Token"]
    r = await auth_client.post("/api/v1/users/me/complete-onboarding")
    assert r.status_code == 403, r.text
