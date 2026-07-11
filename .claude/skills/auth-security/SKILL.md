---
name: auth-security
description: Auth stack. argon2 password hashing, JWT HS256 access (15m), opaque sha256 refresh (7d) in DB, CSRF double-submit, httpOnly cookies. Protected files security.py/cookies.py/dependencies.py.
metadata:
  version: "1.0"
  stack: python-fastapi
  related-skills:
    - fastapi-endpoint
    - redis-caching
tier: 1
triggers:
  - auth
  - jwt
  - refresh
  - csrf
  - cookie
  - login
  - password
  - argon2
summary: |
  Auth = argon2 (passlib) passwords + JWT HS256 access token (15m, httpOnly
  cookie) + opaque refresh token (7d, sha256-hashed in DB, httpOnly) + CSRF
  double-submit (non-httpOnly csrf_token cookie echoed in X-CSRF-Token). Helpers
  in app/core/security.py; cookie set/clear in app/core/cookies.py; guards in
  app/core/dependencies.py. Refresh ROTATES every /auth/refresh (revoke old,
  issue new pair); clear cookies on bad refresh. CSRF bypassed only for
  login/register/refresh. SameSite=lax local, none+Secure in prod. These three
  files are PROTECTED — the hook asks before first edit.
---

# Auth & Security

## Overview

| Aspect       | Details                                                          |
| ------------ | --------------------------------------------------------------- |
| Goal         | Session auth via cookies with CSRF protection and token rotation |
| When         | Login/register/refresh/logout, guards, cookie or token changes   |
| Verification | `uv run pytest -q` (`test_auth.py`)                             |

## Critical rules

**`security.py`, `cookies.py`, `dependencies.py` are PROTECTED — the hook asks before the first edit. Refresh rotates on every `/auth/refresh`. Passwords are argon2. Refresh tokens are stored sha256-hashed, never in plaintext.**

## Concepts

### Passwords (argon2 via passlib)

```python
_pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain: str) -> str: return str(_pwd_ctx.hash(plain))
def verify_password(plain: str, hashed: str) -> bool:
    try: return bool(_pwd_ctx.verify(plain, hashed))
    except Exception: return False
```

### Access token (JWT HS256, 15m)

Encoded with `settings.jwt_secret`; payload carries `sub` (user id), `role`, `type: "access"`, `exp`, `iat`. Stored in the `access_token` httpOnly cookie. `CurrentUser` (in `dependencies.py`) decodes it, verifies `type == "access"`, resolves the user, checks `is_active` — raising raw `HTTPException` (the allowed exception to the DomainError rule, because it is a FastAPI dependency).

### Refresh token (opaque, 7d, hashed in DB)

`generate_refresh_token()` returns `(plain, sha256_digest, expires_at)`. Only the digest is persisted (`RefreshToken.token_hash`); the plaintext goes into the httpOnly `refresh_token` cookie. Lookups hash the incoming plaintext and match the active, non-revoked, unexpired row.

### CSRF double-submit

`generate_csrf_token()` → a non-httpOnly `csrf_token` cookie (JS-readable so the SPA can echo it). `verify_csrf` (a.k.a. `CSRFGuard`) compares the cookie with the `X-CSRF-Token` header via `hmac.compare_digest` on state-changing methods, bypassing `/auth/login`, `/auth/register`, `/auth/refresh` (no session yet).

### Cookies (`app/core/cookies.py`)

`set_auth_cookies` writes all three; `clear_auth_cookies` deletes them. `secure`/`samesite`/`domain` come from settings: SameSite `lax` locally, `none` + `Secure=true` in production for the cross-site Vercel ↔ Render setup. Cookie building lives here and in the auth service only — never in a router.

### Refresh rotation

Every `/auth/refresh`: look up the active token by hash → if missing/invalid, `clear_auth_cookies` + raise `InvalidRefreshError` → else revoke the old token, issue a fresh access+refresh+csrf triple, commit, set cookies.

```python
token = await self.refresh_tokens.get_active_by_hash(hash_refresh_token(refresh_token_plain))
if token is None:
    clear_auth_cookies(response)
    raise InvalidRefreshError
await self.refresh_tokens.revoke(token)
tokens = await self._issue_tokens(user)
await self.session.commit()
self._set_cookies(response, tokens)
```

### Where the layers sit

Cookie IO happens in `AuthService` methods that take a `Response` (the one place a service touches HTTP). Everything else — token creation, hashing, CSRF compare — is pure helpers in `security.py`. Guards (`CurrentUser`, `AdminUser`, `CSRFGuard`) are dependencies in `dependencies.py`.

## Patterns

### Add a protected endpoint

1. Inject `CurrentUser` (or `AdminUser`).
2. State-changing routes are covered by the global `CSRFGuard`; the client must send `X-CSRF-Token` matching the cookie.
3. Add a `RateLimiter` on auth-adjacent POSTs (auth endpoints use 10/60s).

### Change token/cookie behavior

1. Touch `security.py`/`cookies.py`/`dependencies.py` — acknowledge the protected-file prompt.
2. Keep refresh rotation and the sha256-hashed-at-rest invariant intact.
3. Update `test_auth.py` (register/login/refresh/logout flows).

## Common mistakes

| Mistake | Fix |
| ------- | --- |
| Storing the refresh token plaintext | Store `hash_refresh_token(...)`; cookie holds plaintext |
| Not rotating on refresh | Revoke old, issue a new pair every time |
| CSRF cookie httpOnly | `csrf_token` must be JS-readable (httpOnly=False) |
| Raising `HTTPException` in a service | Use `DomainError`; raw HTTP only in `dependencies.py` guards |
| SameSite=lax in prod cross-site | `none` + `Secure=true` in production |
| `==` on CSRF/token compare | `hmac.compare_digest` |

## Checklist

- [ ] Passwords argon2; refresh tokens sha256 in DB
- [ ] Refresh rotates (old revoked, new pair issued)
- [ ] CSRF cookie non-httpOnly; guard on state-changing routes
- [ ] Cookie IO only in the auth service / `cookies.py`
- [ ] Protected-file edit acknowledged; `test_auth.py` updated
