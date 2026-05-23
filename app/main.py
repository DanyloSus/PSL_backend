from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import dispose_engine, get_sessionmaker
from app.core.logging import configure_logging
from app.core.redis import close_redis, get_redis_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log = structlog.get_logger()
    settings = get_settings()
    log.info("app.start", env=settings.env)
    # Warm singletons.
    get_sessionmaker()
    get_redis_client()
    try:
        yield
    finally:
        log.info("app.stop")
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
