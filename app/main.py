from contextlib import asynccontextmanager
import os
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import health, places, itineraries
from app.core.config import settings
from app.core.logging import setup_logging

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.seed import seed_places_if_empty  # Usiamo la tua funzione originale

# Import dei modelli SQLAlchemy per registrarli su Base.metadata
from app.db.models import place as _place_model  # noqa: F401
from app.db.models import itinerary as _itinerary_model  # noqa: F401

from app.api import debug


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestisce l'avvio e lo spegnimento dell'app.
    Esegue il seeding dei dati se il database è vuoto.
    """
    git_sha = os.getenv("GIT_SHA", "unknown")
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"🚀 API startup (git_sha={git_sha})")

    # In locale con SQLite crea le tabelle, su AWS ci pensa Alembic nel Dockerfile
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    # Avvio del seeding automatico
    db = SessionLocal()
    try:
        logger.info("Checking database for seeding...")
        # Usiamo la tua funzione che è già configurata correttamente
        seed_places_if_empty(db)
        logger.info("Database check/seeding completed.")
    except Exception as e:
        logger.error(f"❌ Error during startup seeding: {e}")
    finally:
        db.close()

    yield

    logger.info("🛑 API shutting down...")
    engine.dispose()
    logger.info("✅ Shutdown completato.")


def create_app() -> FastAPI:
    """Inizializza e configura l'istanza FastAPI.""" 
    setup_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(places.router)
    app.include_router(itineraries.router)
    app.include_router(debug.router)

    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    
    return app


app = create_app()