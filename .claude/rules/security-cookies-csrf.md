---
id: security-cookies-csrf
tier: 1
tooling: [convention]
enforcement: strict
paths:
  - "app/core/security.py"
  - "app/core/cookies.py"
  - "app/core/dependencies.py"
  - "app/services/auth_service.py"
---

# Security — Cookies / CSRF / JWT

Enforces the auth token scheme, cookie flags, and CSRF double-submit. `security.py`, `cookies.py`, and `dependencies.py` are protected files — change them deliberately.

## Rules

### SE1. Password hashing with argon2

**Tooling:** `convention`

Hash and verify passwords through the argon2 helpers in `app/core/security.py` (passlib). Never store plaintext, never roll your own hashing, never compare with `==`.

```python
# ❌ FORBIDDEN
if user.password_hash == password: ...

# ✅ CORRECT
if not verify_password(password, user.password_hash):
    raise InvalidCredentialsError()
```

**Why:** argon2 is the chosen, memory-hard KDF. Any deviation weakens credential security or leaks timing.

### SE2. Access = JWT HS256 (15m); refresh = opaque, sha256 in DB (7d)

**Tooling:** `convention`

`access_token` is a 15-minute HttpOnly JWT (HS256). `refresh_token` is a 7-day HttpOnly opaque token stored as its sha256 hash in the DB (never the raw value). `csrf_token` is non-HttpOnly for double-submit.

```python
# ❌ FORBIDDEN — storing the raw refresh token
await self.refresh_tokens.create(user_id=user.id, token=raw_token)

# ✅ CORRECT — store only the hash
await self.refresh_tokens.create(user_id=user.id, token_hash=sha256_hex(raw_token))
```

**Why:** A short-lived access token limits blast radius; hashed refresh tokens mean a DB leak can't be replayed as sessions.

### SE3. Refresh rotates on every `/auth/refresh`

**Tooling:** `convention`

Each refresh revokes the old token and issues a new pair. On a bad/expired refresh, call `clear_auth_cookies`.

```python
# ✅ CORRECT
await self.refresh_tokens.revoke(old_token_hash)
new_pair = self._issue_tokens(user)  # new access + refresh
```

**Why:** Rotation detects token theft (a reused old token is now invalid) and bounds the lifetime of any single credential.

### SE4. CSRF double-submit; bypass only login/register/refresh

**Tooling:** `convention`

All state-changing requests (POST/PUT/PATCH/DELETE) require the `X-CSRF-Token` header to match the `csrf_token` cookie. The guard is bypassed only for `/auth/login`, `/auth/register`, `/auth/refresh` (no session exists yet).

```python
# ✅ CORRECT — guard compares header to cookie for state-changing methods
if request.method in _STATE_CHANGING and request.url.path not in _CSRF_EXEMPT:
    if not csrf_tokens_match(header_token, cookie_token):
        raise HTTPException(status_code=403, detail="csrf mismatch")
```

**Why:** Double-submit blocks cross-site request forgery. The three exempt endpoints have no session to protect yet, so requiring the header there would be impossible.

### SE5. Cookie flags: SameSite lax local / none+Secure prod

**Tooling:** `convention`

Set cookies through `app/core/cookies.py`. `SameSite` defaults to `lax` locally; production must be `none` with `Secure=true` for the cross-site Vercel ↔ Render setup.

```python
# ✅ CORRECT — flags come from settings, HttpOnly on auth tokens
response.set_cookie(
    "access_token", token, httponly=True,
    samesite=settings.cookie_samesite, secure=settings.cookie_secure,
)
```

**Why:** Cross-site cookies require `SameSite=None; Secure`; getting this wrong silently drops auth cookies in production.

## Verification

```bash
uv run pytest -q app/tests -k "auth or csrf or refresh"
```
