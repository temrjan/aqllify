import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.auth.router import router as auth_router
from src.lessons.router import router as lessons_router
from src.progress.router import router as progress_router
from src.config import settings

# Configure structlog: JSON in prod (machine-parseable), pretty console in dev.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.dev.ConsoleRenderer()
        if settings.is_development
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("aqllify_starting", env=settings.app_env)
    yield
    logger.info("aqllify_shutdown")


app = FastAPI(
    title="Aqllify API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "https://aqllify.com",
        "https://app.aqllify.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Telegram-InitData"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log every API request: method, path, status, duration. Skip /health."""
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path == "/health":
        return response
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
        client=request.client.host if request.client else None,
    )
    return response


# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(lessons_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
