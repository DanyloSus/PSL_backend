# ADR 0010 — Pinned `fastapi-limiter==0.1.6`

- **Status:** Accepted
- **Date:** 2026-05-24

## Context

We use `fastapi-limiter` for Redis-backed rate limits on `/auth/{register,login,refresh}` and `/activities/log`. The library is small and not particularly active.

Version 0.2.0 rewrote the public API: the `RateLimiter` class no longer accepts `times` and `seconds` keyword arguments, and the `FastAPILimiter` initializer was reshuffled. Upgrading required wrapping `pyrate_limiter.Limiter` instances by hand.

Our routers were written against the 0.1.6 API (`Depends(RateLimiter(times=10, seconds=60))`), which is also the API documented in the broader FastAPI ecosystem.

## Decision

- Pin `fastapi-limiter==0.1.6` exactly in `pyproject.toml` (not `>=0.1.6`).
- mypy override for the package (no published stubs).
- Do not adopt 0.2.x until either (a) we have an explicit need for its features or (b) it stabilises further.

## Consequences

**Positive**
- Existing rate-limit code keeps working.
- No urgent migration when other deps push for an upgrade.

**Negative**
- We will eventually accumulate dependency-graph friction (e.g. when another package pins `redis>=5.x` in a way 0.1.6 dislikes).
- We may miss bugfixes shipped in 0.2.x.

## Compliance

- Do not relax the pin (`==0.1.6`) without revisiting the routers that use `RateLimiter(times=..., seconds=...)`.
- If a future ADR supersedes this one, rewrite the call sites at the same time.
