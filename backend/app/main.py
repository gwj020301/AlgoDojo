"""FastAPI application entrypoint.

Exposes liveness (``/health``) and readiness (``/health/ready``) endpoints.
Readiness verifies connectivity to PostgreSQL and Redis.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.config import get_settings
from app.db import check_database, engine
from app.learning.router import router as learning_router
from app.problems.router import router as problems_router
from app.progress.router import router as progress_router
from app.redis_client import check_redis, redis_client
from app.submissions.router import router as submissions_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage startup/shutdown: dispose engine and close Redis on exit."""
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(submissions_router)
app.include_router(problems_router)
app.include_router(progress_router)
app.include_router(learning_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe: process is up."""
    return {"status": "ok", "env": settings.env}


@app.get("/health/ready", tags=["health"])
async def health_ready() -> dict[str, object]:
    """Readiness probe: dependencies (DB, Redis) are reachable."""
    checks: dict[str, str] = {}

    try:
        checks["database"] = "ok" if await check_database() else "fail"
    except Exception as exc:  # noqa: BLE001 - report any connectivity error
        checks["database"] = f"fail: {exc.__class__.__name__}"

    try:
        checks["redis"] = "ok" if await check_redis() else "fail"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"fail: {exc.__class__.__name__}"

    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
