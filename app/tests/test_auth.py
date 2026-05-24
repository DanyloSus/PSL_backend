from __future__ import annotations

from httpx import AsyncClient


async def test_register_creates_user_and_sets_cookies(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "username": "alice", "password": "pw_secret1"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user"]["email"] == "a@b.com"
    assert data["user"]["role"] == "USER"
    assert data["user"]["global_xp"] == 0
    assert data["user"]["global_level"] == 1
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies
    assert "csrf_token" in resp.cookies


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    payload = {"email": "x@y.com", "username": "user_x", "password": "pw_secret1"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    payload2 = {**payload, "username": "user_y"}
    r2 = await client.post("/api/v1/auth/register", json=payload2)
    assert r2.status_code == 409


async def test_login_and_me(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "l@m.com", "username": "user_lm", "password": "pw_secret1"},
    )
    # Clear cookies and login fresh.
    client.cookies.clear()
    r = await client.post("/api/v1/auth/login", json={"email": "l@m.com", "password": "pw_secret1"})
    assert r.status_code == 200
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "l@m.com"


async def test_login_bad_password_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "b@p.com", "username": "user_bp", "password": "pw_secret1"},
    )
    client.cookies.clear()
    r = await client.post("/api/v1/auth/login", json={"email": "b@p.com", "password": "wrong"})
    assert r.status_code == 401


async def test_refresh_rotates_token(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "r@t.com", "username": "user_rt", "password": "pw_secret1"},
    )
    old = client.cookies.get("refresh_token")
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    new = client.cookies.get("refresh_token")
    assert old and new and old != new


async def test_logout_requires_csrf(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "lo@u.com", "username": "user_lou", "password": "pw_secret1"},
    )
    # Without CSRF header → 403.
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 403
    csrf = client.cookies.get("csrf_token") or ""
    r2 = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert r2.status_code == 204
