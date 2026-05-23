from __future__ import annotations

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    assert r.status_code == 200, r.text
    templates = r.json()
    matches = [t for t in templates if t["title"] == title]
    assert matches, f"template {title!r} not seeded; got {[t['title'] for t in templates]}"
    return dict(matches[0])


async def test_list_activities_includes_seeded(auth_client: AsyncClient) -> None:
    r = await auth_client.get("/api/v1/activities")
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert "Workout (gym)" in titles
    assert "Alcohol" in titles
    assert len(titles) >= 15


async def test_log_positive_quantity_multiplies_xp(auth_client: AsyncClient) -> None:
    workout = await _template(auth_client, "Workout (gym)")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 2},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    by_key = {a["stat"]["key"]: a for a in data["applied"]}
    assert by_key["strength"]["xp_applied"] == 20
    assert by_key["strength"]["xp"] == 20
    assert by_key["health"]["xp_applied"] == 6
    assert by_key["endurance"]["xp_applied"] == 4
    assert data["global_xp"] == 30
    assert data["global_level"] == 1


async def test_binary_forces_quantity_to_one(auth_client: AsyncClient) -> None:
    alcohol = await _template(auth_client, "Alcohol")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": alcohol["id"], "quantity": 99},
    )
    assert r.status_code == 200
    data = r.json()
    by_key = {a["stat"]["key"]: a for a in data["applied"]}
    # Sent 99 but BINARY → quantity = 1. social_skills +3.
    assert by_key["social_skills"]["xp_applied"] == 3


async def test_negative_xp_floors_at_zero(auth_client: AsyncClient) -> None:
    alcohol = await _template(auth_client, "Alcohol")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": alcohol["id"], "quantity": 1},
    )
    assert r.status_code == 200
    data = r.json()
    by_key = {a["stat"]["key"]: a for a in data["applied"]}
    # Health was 0; -10 raw, floored, actual delta = 0, xp stays 0.
    assert by_key["health"]["xp"] == 0
    assert by_key["health"]["xp_applied"] == 0


async def test_level_up_emits_flag(auth_client: AsyncClient) -> None:
    workout = await _template(auth_client, "Workout (gym)")
    # Strength +10 per qty. Need 100 xp to reach L2, so qty=10 → 100 xp.
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 10},
    )
    assert r.status_code == 200
    data = r.json()
    strength = next(a for a in data["applied"] if a["stat"]["key"] == "strength")
    assert strength["level"] == 2
    assert strength["leveled_up"] is True


async def test_activity_history_records_log(auth_client: AsyncClient) -> None:
    workout = await _template(auth_client, "Workout (gym)")
    await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 1},
    )
    r = await auth_client.get("/api/v1/users/me/activity-history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["quantity"] == 1
    assert data[0]["total_xp_applied"] == 15  # 10+3+2
    assert len(data[0]["effects"]) == 3
