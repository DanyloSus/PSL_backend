from __future__ import annotations

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    matches = [t for t in r.json() if t["title"] == title]
    assert matches, f"template {title!r} not seeded"
    return dict(matches[0])


async def test_history_entry_is_enriched(auth_client: AsyncClient) -> None:
    # @trace FR-HISTORY-1
    workout = await _template(auth_client, "Workout (gym)")
    await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 1},
    )
    r = await auth_client.get("/api/v1/users/me/activity-history")
    assert r.status_code == 200, r.text
    entry = r.json()["items"][0]
    assert entry["title"] == "Workout (gym)"
    assert "description" in entry
    assert entry["input_type"] == "QUANTITY"
    for effect in entry["effects"]:
        assert effect["key"]
        assert effect["display_name"]
        assert "icon" in effect
