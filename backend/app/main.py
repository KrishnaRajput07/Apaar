"""
APAAR Pramaan — FastAPI main application.
Modular monolith with all routers wired in.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import engine, Base, create_all_tables
from .routers import auth, institutions, students, seats, cases, credentials, audit, analytics, integrity


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables if they don't exist."""
    # Try to create tables (won't fail if they already exist)
    try:
        create_all_tables()
    except Exception:
        pass  # DB might not be ready in dev — tables created by seeder
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="National Student Identity & Integrity Platform — SIMULATION",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
app.include_router(auth.router,           prefix="/api/v1")
app.include_router(institutions.router,    prefix="/api/v1")
app.include_router(students.router,         prefix="/api/v1")
app.include_router(seats.router,            prefix="/api/v1")
app.include_router(cases.router,            prefix="/api/v1")
app.include_router(credentials.router,      prefix="/api/v1")
app.include_router(audit.router,            prefix="/api/v1")
app.include_router(analytics.router,        prefix="/api/v1")
app.include_router(integrity.router,        prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok",
        "docs": "/docs",
        "label": "SIMULATION — not a real government system",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
