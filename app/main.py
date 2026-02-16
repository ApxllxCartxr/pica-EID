"""
PRISMID — Personnel Identity and Role Governance System
Main FastAPI application entry point.

All API endpoints are mounted under /api/v1 for versioning.
External applications can authenticate via X-API-Key header.
"""

import json
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os

from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: F401,F403 — Import all models for table creation
from app.core.rate_limiter import limiter
from app.core.middleware import RequestIdMiddleware, IdempotencyMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Personnel Identity and Role Governance System.\n\n"
        "### Authentication\n"
        "- **Admin Panel**: Use `/api/v1/auth/login` to obtain a JWT Bearer token.\n"
        "- **External Apps**: Include an `X-API-Key` header with every request.\n\n"
        "### Versioning\n"
        "All endpoints live under `/api/v1`."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# --- Rate Limiter ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Global exception handler for consistent JSON errors ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: return a structured JSON error instead of an HTML 500."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
        },
    )


# --- Middleware (order matters: outermost first) ---
app.add_middleware(RequestIdMiddleware)
app.add_middleware(IdempotencyMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-Idempotent-Replay"],
)

# Trusted-host protection (only if configured)
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )


# ---------------------------------------------------------------------------
# API v1 router — all endpoints live here
# ---------------------------------------------------------------------------
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.roles import router as roles_router
from app.api.audit import router as audit_router
from app.api.divisions import router as divisions_router
from app.api.domains import router as domains_router
from app.api.sheets import router as sheets_router
from app.api.dashboard import router as dashboard_router
from app.api.api_keys import router as api_keys_router

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(roles_router)
v1_router.include_router(audit_router)
v1_router.include_router(divisions_router)
v1_router.include_router(domains_router)
v1_router.include_router(sheets_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(api_keys_router)

app.include_router(v1_router)


# --- Health check (no versioning — always available) ---
@app.get("/api/health", tags=["Health"])
async def health():
    """Health check with DB and Redis status."""
    health_status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"

    return health_status


# --- Serve static files ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# --- Serve dashboard SPA ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>PRISMID Dashboard</h1><p>Static files not found.</p>")


# --- Create tables on startup (development) ---
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
