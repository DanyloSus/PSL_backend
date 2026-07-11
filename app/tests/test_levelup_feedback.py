from __future__ import annotations

from httpx import AsyncClient


async def _template(client: AsyncClient, title: str) -> dict[str, object]:
    r = await client.get("/api/v1/activities")
    assert r.status_code == 200, r.text
    matches = [t for t in r.json() if t["title"] == title]
    assert matches, f"template {title!r} not seeded"
    return dict(matches[0])


async def test_per_stat_progress_fields_present(auth_client: AsyncClient) -> None:
    # @trace FR-LEVELUP-1
    workout = await _template(auth_client, "Workout (gym)")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 1},
    )
    assert r.status_code == 200, r.text
    strength = next(a for a in r.json()["applied"] if a["stat"]["key"] == "strength")
    for field in ("xp_into_level", "xp_for_next", "previous_level", "levels_gained"):
        assert field in strength


async def test_levels_gained_on_multi_level_jump(auth_client: AsyncClient) -> None:
    # @trace FR-LEVELUP-1
    workout = await _template(auth_client, "Workout (gym)")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 30},
    )
    assert r.status_code == 200, r.text
    strength = next(a for a in r.json()["applied"] if a["stat"]["key"] == "strength")
    assert strength["previous_level"] == 1
    assert strength["level"] == strength["previous_level"] + strength["levels_gained"]
    assert strength["levels_gained"] >= 1
    assert strength["leveled_up"] is True


async def test_no_level_change_reports_zero(auth_client: AsyncClient) -> None:
    # @trace FR-LEVELUP-1
    workout = await _template(auth_client, "Workout (gym)")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 1},
    )
    strength = next(a for a in r.json()["applied"] if a["stat"]["key"] == "strength")
    assert strength["levels_gained"] == 0
    assert strength["leveled_up"] is False


async def test_global_progress_fields_present(auth_client: AsyncClient) -> None:
    # @trace FR-LEVELUP-2
    workout = await _template(auth_client, "Workout (gym)")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": workout["id"], "quantity": 10},
    )
    data = r.json()
    for field in (
        "xp_into_level",
        "xp_for_next",
        "previous_global_level",
        "global_levels_gained",
    ):
        assert field in data
    assert data["global_level"] == data["previous_global_level"] + data["global_levels_gained"]
    assert data["global_leveled_up"] is True


async def test_negative_log_never_negative_gain(auth_client: AsyncClient) -> None:
    # @trace FR-LEVELUP-3
    alcohol = await _template(auth_client, "Alcohol")
    r = await auth_client.post(
        "/api/v1/activities/log",
        json={"activityTemplateId": alcohol["id"], "quantity": 1},
    )
    data = r.json()
    assert data["global_levels_gained"] == 0
    for applied in data["applied"]:
        assert applied["levels_gained"] == 0
        assert applied["level"] >= applied["previous_level"]
