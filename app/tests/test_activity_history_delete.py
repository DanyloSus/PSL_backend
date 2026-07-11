from __future__ import annotations

import uuid

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    matches = [t for t in r.json() if t["title"] == title]
    assert matches, f"template {title!r} not seeded"
    return dict(matches[0])


async def _log_and_get_id(client: AsyncClient, template_id: str, quantity: int) -> str:
    r = await client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": template_id, "quantity": quantity},
    )
    assert r.status_code == 200, r.text
    hist = await client.get("/api/v1/users/me/activity-history")
    return str(hist.json()["items"][0]["id"])


async def _stat(client: AsyncClient, key: str) -> dict[str, object]:
    r = await client.get("/api/v1/users/me/stats")
    return next(s for s in r.json() if s["stat"]["key"] == key)


async def test_delete_reverses_xp(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-4
    workout = await _template(auth_client, "Workout (gym)")
    log_id = await _log_and_get_id(auth_client, str(workout["id"]), 1)

    r = await auth_client.delete(f"/api/v1/users/me/activity-history/{log_id}")
    assert r.status_code == 204, r.text

    assert (await _stat(auth_client, "strength"))["xp"] == 0
    hist = await auth_client.get("/api/v1/users/me/activity-history")
    assert hist.json()["total"] == 0

    me = await auth_client.get("/api/v1/users/me")
    assert me.json()["global_xp"] == 0


async def test_delete_does_not_lower_level(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-4
    workout = await _template(auth_client, "Workout (gym)")
    log_id = await _log_and_get_id(auth_client, str(workout["id"]), 10)
    assert (await _stat(auth_client, "strength"))["level"] == 2

    r = await auth_client.delete(f"/api/v1/users/me/activity-history/{log_id}")
    assert r.status_code == 204

    strength = await _stat(auth_client, "strength")
    assert strength["xp"] == 0
    assert strength["level"] == 2


async def test_delete_unknown_log_returns_404(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-5
    r = await auth_client.delete(f"/api/v1/users/me/activity-history/{uuid.uuid4()}")
    assert r.status_code == 404, r.text


async def test_delete_foreign_log_returns_404(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-5
    workout = await _template(auth_client, "Workout (gym)")
    log_id = await _log_and_get_id(auth_client, str(workout["id"]), 1)

    reg = await auth_client.post(
        "/api/v1/auth/register",
        json={"email": "intruder@psl.io", "username": "intruder", "password": "secret123"},
    )
    assert reg.status_code == 201
    auth_client.headers["X-CSRF-Token"] = auth_client.cookies.get("csrf_token") or ""

    forbidden = await auth_client.delete(f"/api/v1/users/me/activity-history/{log_id}")
    assert forbidden.status_code == 404, forbidden.text

    back = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "tester@psl.io", "password": "secret123"},
    )
    assert back.status_code == 200
    auth_client.headers["X-CSRF-Token"] = auth_client.cookies.get("csrf_token") or ""
    hist = await auth_client.get("/api/v1/users/me/activity-history")
    assert hist.json()["total"] == 1


async def test_delete_requires_auth(client: AsyncClient) -> None:
    # @trace NFR-HISTORY-1
    client.cookies.set("csrf_token", "abc")
    client.headers["X-CSRF-Token"] = "abc"
    r = await client.delete(f"/api/v1/users/me/activity-history/{uuid.uuid4()}")
    assert r.status_code == 401, r.text


async def test_delete_requires_csrf(auth_client: AsyncClient) -> None:
    # @trace NFR-HISTORY-1
    del auth_client.headers["X-CSRF-Token"]
    r = await auth_client.delete(f"/api/v1/users/me/activity-history/{uuid.uuid4()}")
    assert r.status_code == 403, r.text
