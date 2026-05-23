from __future__ import annotations

from httpx import AsyncClient


async def test_user_stats_auto_created_on_register(auth_client: AsyncClient) -> None:
    r = await auth_client.get("/api/v1/users/me/stats")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 7
    keys = {s["stat"]["key"] for s in data}
    assert keys == {
        "strength",
        "health",
        "intelligence",
        "mental_state",
        "endurance",
        "finance",
        "social_skills",
    }
    for s in data:
        assert s["xp"] == 0
        assert s["level"] == 1
        assert s["xp_for_next"] == 100


async def test_users_me_returns_profile(auth_client: AsyncClient) -> None:
    r = await auth_client.get("/api/v1/users/me")
    assert r.status_code == 200
    data = r.json()
    assert data["global_xp"] == 0
    assert data["global_level"] == 1
