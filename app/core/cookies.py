from __future__ import annotations

from fastapi import Response

from app.core.config import get_settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


def _common_kwargs() -> dict[str, object]:
    s = get_settings()
    kw: dict[str, object] = {
        "secure": s.cookie_secure,
        "samesite": s.cookie_samesite,
        "path": "/",
    }
    if s.cookie_domain:
        kw["domain"] = s.cookie_domain
    return kw


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    s = get_settings()
    common = _common_kwargs()
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        max_age=s.jwt_access_ttl_seconds,
        **common,  # type: ignore[arg-type]
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        max_age=s.jwt_refresh_ttl_seconds,
        **common,  # type: ignore[arg-type]
    )
    # CSRF cookie readable by JS so frontend can echo it in X-CSRF-Token header.
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        httponly=False,
        max_age=s.jwt_refresh_ttl_seconds,
        **common,  # type: ignore[arg-type]
    )


def clear_auth_cookies(response: Response) -> None:
    common = _common_kwargs()
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, **common)  # type: ignore[arg-type]
