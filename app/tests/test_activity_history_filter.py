from __future__ import annotations

import asyncio

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    matches = [t for t in r.json() if t["title"] == title]
    assert matches, f"template {title!r} not seeded"
    return dict(matches[0])


async def _log(client: AsyncClient, template_id: str, quantity: int = 1) -> None:
    r = await client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": template_id, "quantity": quantity},
    )
    assert r.status_code == 200, r.text
    await asyncio.sleep(0.02)


async def test_filter_by_template(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-2
    workout = await _template(auth_client, "Workout (gym)")
    run = await _template(auth_client, "Run")
    await _log(auth_client, str(workout["id"]))
    await _log(auth_client, str(run["id"]))

    r = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"template_id": str(workout["id"])},
    )
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["activity_template_id"] == str(workout["id"])


async def test_filter_by_date_range(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-2
    workout = await _template(auth_client, "Workout (gym)")
    await _log(auth_client, str(workout["id"]))

    full = await auth_client.get("/api/v1/users/me/activity-history")
    created = full.json()["items"][0]["created_at"]

    included = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"from": created},
    )
    assert len(included.json()["items"]) == 1

    excluded = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"to": "2000-01-01T00:00:00Z"},
    )
    assert len(excluded.json()["items"]) == 0


async def test_filter_composes_with_limit(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-2
    workout = await _template(auth_client, "Workout (gym)")
    await _log(auth_client, str(workout["id"]))
    await _log(auth_client, str(workout["id"]))

    r = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"template_id": str(workout["id"]), "limit": 1},
    )
    data = r.json()
    assert len(data["items"]) == 1
    assert data["total"] == 2
    assert data["has_more"] is True
