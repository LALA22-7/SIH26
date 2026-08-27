"""CycloneWatch FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import dispose_engine

# Routers — imported here; more added as tasks complete
from app.api.health import router as health_router
from app.api.frames import router as frames_router
from app.api.classify import router as classify_router
from app.api.predict import router as predict_router
from app.api.replay import router as replay_router
from app.api.metrics import router as metrics_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage DB connection pool lifecycle."""
    # Startup: the engine pool is created lazily on first use,
    # but we can do an explicit startup check here.
    yield
    # Shutdown: dispose of the async engine pool cleanly.
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="CycloneWatch API",
        description=(
            "AI/ML-based cyclone identification, classification, and prediction "
            "system for PS70 — SIH 2026."
        ),
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    origins = settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(health_router)
    app.include_router(frames_router)
    app.include_router(classify_router)
    app.include_router(predict_router)
    app.include_router(replay_router)
    app.include_router(metrics_router)

    return app


app = create_app()
