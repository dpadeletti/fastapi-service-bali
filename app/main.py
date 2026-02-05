from contextlib import asynccontextmanager
import os
import logging

from fastapi import FastAPI

from app.api import health, places, itineraries
from app.core.config import settings
from app.core.logging import setup_logging

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.seed import seed_places_if_empty

# Import dei modelli SQLAlchemy per registrarli su Base.metadata
from app.db.models import place as _place_model  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    git_sha = os.getenv("GIT_SHA", "unknown")
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"🚀 API startup (git_sha={git_sha})")

    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_places_if_empty(db)
    finally:
        db.close()

    yield

    # Shutdown (se in futuro servirà: chiudere risorse, connessioni, ecc.)


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(places.router)
    app.include_router(itineraries.router)

    return app


app = create_app()