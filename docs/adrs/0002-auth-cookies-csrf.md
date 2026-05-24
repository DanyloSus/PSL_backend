# ADR 0002 — Auth: JWT access + DB-tracked opaque refresh in httpOnly cookies

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

The frontend ships on Vercel and the backend on Render. They live on different registrable domains, so cookies are cross-site. We need:

- A fast path for authentication on every request (cheap to verify, no DB hit).
- A revocable way to keep users logged in for days without re-entering credentials.
- Defense against XSS leaking the token.
- Defense against CSRF on state-changing requests.

Candidates considered:

1. **Stateless JWT access + JWT refresh** — simple, no DB. Cannot revoke individual sessions before expiry. Bad for "log me out everywhere" or post-password-reset cleanup.
2. **Stateless JWT access + DB-tracked opaque refresh** *(chosen)* — short-lived JWT for the hot path, long-lived random token stored hashed in DB. Revocable.
3. **Sessions in Redis** — works but couples request auth to Redis availability and adds a network hop for every authenticated call.

Storage:

- **`Authorization: Bearer`** — easy CSRF model but exposes the access token to JS / XSS.
- **httpOnly cookies** *(chosen)* — protects the token from JS, costs us CSRF protection.

## Decision

Tokens:

- **Access token** — JWT HS256 signed with `JWT_SECRET`, 15-minute TTL, claims: `sub` (UUID), `role`, `type=access`, `exp`, `iat`.
- **Refresh token** — opaque `secrets.token_urlsafe(48)`, sha256-hashed and persisted in `refresh_tokens` table with `user_id`, `expires_at` (7 days), nullable `revoked_at`. Rotated on every `/auth/refresh`: the consumed token is revoked and a new pair is issued.
- **CSRF token** — random `secrets.token_urlsafe(32)`. Sent both as a non-HttpOnly cookie (JS can read it) and required as `X-CSRF-Token` header on every POST/PUT/PATCH/DELETE except `/auth/{login,register,refresh}`. Compared with `hmac.compare_digest`.

Cookies (`app/core/cookies.py`):

- `access_token` — HttpOnly, `max_age = JWT_ACCESS_TTL_SECONDS`
- `refresh_token` — HttpOnly, `max_age = JWT_REFRESH_TTL_SECONDS`
- `csrf_token` — non-HttpOnly, `max_age = JWT_REFRESH_TTL_SECONDS`

All three share `path=/`, `domain=COOKIE_DOMAIN`, `samesite=COOKIE_SAMESITE`, `secure=COOKIE_SECURE`. Local default: `samesite=lax`, `secure=false`. Production: `samesite=none`, `secure=true` (cross-site requirement).

Password hashing: argon2 via passlib (`CryptContext(schemes=["argon2"])`).

## Consequences

**Positive**
- Access token verification is a single HS256 decode — no DB round-trip on the hot path.
- Refresh tokens can be revoked individually (logout) or in bulk (`logout_all_for_user`). Compromised user → invalidate every refresh token without rotating `JWT_SECRET`.
- httpOnly cookies stop a cross-site script from siphoning the tokens.
- CSRF double-submit closes the cookie-auth attack surface for state-changing requests. Login/register/refresh themselves are CSRF-safe because they ignore the cookie value (the user does not yet have a session).

**Negative**
- Cookies must be CORS-credentialed (`allow_credentials=True`) and the frontend has to send `credentials: 'include'` on every request. Trade-off accepted for the security gain.
- Refresh-token rotation requires the DB on every refresh. Acceptable: it's a low-frequency operation compared to access verification.
- CSRF tokens add one extra cookie + one extra header on every state-changing request. Frontend reads the cookie and adds the header automatically; the cost is negligible.

## Compliance

- Never log raw refresh tokens or password hashes.
- Never accept a refresh token in a query string or body — cookie only.
- Adding a new state-changing endpoint outside `/api/v1/auth/{login,register,refresh}` automatically gets CSRF enforcement via `Depends(verify_csrf)` on the router include.
