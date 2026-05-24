from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import dispose_engine, get_sessionmaker
from app.core.dependencies import verify_csrf
from app.core.exceptions import DomainError
from app.core.logging import configure_logging
from app.core.redis import close_redis, get_redis_client
from app.routers import activities as activities_router
from app.routers import auth as auth_router
from app.routers import users as users_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log = structlog.get_logger()
    settings = get_settings()
    log.info("app.start", env=settings.env)
    get_sessionmaker()
    redis = get_redis_client()
    await FastAPILimiter.init(redis)
    try:
        yield
    finally:
        log.info("app.stop")
        await FastAPILimiter.close()
        await dispose_engine()
        await close_redis()


app = FastAPI(title="PSL Backend", version="0.1.0", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    status = "ok"
    db_status = "ok"
    redis_status = "ok"
    try:
        sm = get_sessionmaker()
        async with sm() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"
        status = "degraded"
    try:
        pong = get_redis_client().ping()
        if hasattr(pong, "__await__"):
            await pong
    except Exception:
        redis_status = "down"
        status = "degraded"
    return {"status": status, "db": db_status, "redis": redis_status}


app.include_router(
    auth_router.router,
    prefix="/api/v1",
    dependencies=[Depends(verify_csrf)],
)
app.include_router(
    users_router.router,
    prefix="/api/v1",
    dependencies=[Depends(verify_csrf)],
)
app.include_router(
    activities_router.router,
    prefix="/api/v1",
    dependencies=[Depends(verify_csrf)],
)
