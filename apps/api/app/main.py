"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db, init_db
from app.models import Opportunity
from app.routes.ingest import router as ingest_router
from app.routes.opportunities import router as opportunities_router
from app.services.ingest import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    if settings.enable_demo_seed:
        db: Session = SessionLocal()
        try:
            existing_count = db.scalar(select(func.count()).select_from(Opportunity)) or 0
            if existing_count == 0:
                seed_demo_data(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title="PhD Opportunity Tracker API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(opportunities_router)
app.include_router(ingest_router)


@app.get("/health")
def healthcheck(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
