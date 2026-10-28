from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.db.session import engine, Base, SessionLocal
from app.api import auth, cases, institutions, dashboard, notifications, coordination, reports, users, bureaus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed if empty and enabled
    if settings.SEED_DEMO_DATA:
        from app.db.seed import seed_if_empty
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    # Ensure upload dir
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="INSTITRACK API",
    description="Integrated Institutional Case Tracking, Intelligence and Coordination Platform — SIH Demonstration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc) if settings.DEBUG else "An error occurred"},
    )


app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(institutions.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(coordination.router)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(bureaus.router)


@app.get("/")
def root():
    return {
        "app": "INSTITRACK",
        "tagline": "One Institution. Connected Cases. Smarter Decisions.",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
