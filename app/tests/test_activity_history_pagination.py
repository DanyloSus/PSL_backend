from __future__ import annotations

import asyncio

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    matches = [t for t in r.json() if t["title"] == title]
    assert matches, f"template {title!r} not seeded"
    return dict(matches[0])


async def _log(client: AsyncClient, template_id: str) -> None:
    r = await client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": template_id, "quantity": 1},
    )
    assert r.status_code == 200, r.text
    await asyncio.sleep(0.02)


async def test_pagination_metadata_first_page(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-3
    workout = await _template(auth_client, "Workout (gym)")
    for _ in range(3):
        await _log(auth_client, str(workout["id"]))

    r = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"limit": 2},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["has_more"] is True
    assert data["next_before"] is not None


async def test_pagination_last_page(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-3
    workout = await _template(auth_client, "Workout (gym)")
    for _ in range(3):
        await _log(auth_client, str(workout["id"]))

    first = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"limit": 2},
    )
    next_before = first.json()["next_before"]

    second = await auth_client.get(
        "/api/v1/users/me/activity-history",
        params={"limit": 2, "before": next_before},
    )
    data = second.json()
    assert len(data["items"]) == 1
    assert data["has_more"] is False
    assert data["next_before"] is None
