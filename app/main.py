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
from app.db.models import itinerary as _itinerary_model  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan per l'app FastAPI.
    Gestisce le operazioni di avvio e spegnimento dell'applicazione.
    
    Durante lo startup:
    1. Registra la versione del codice (GIT_SHA).
    2. Crea le tabelle se si usa SQLite.
    3. Esegue il seeding dei dati iniziali dei luoghi.
    
    """
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

    # Shutdown
    logger.info("🛑 API shutting down...")
    # Qui potresti chiudere connessioni a Redis, inviare un segnale
    # a un sistema di monitoraggio o semplicemente loggare la chiusura.
    # Utile se passi a DB più complessi come PostgreSQL
    engine.dispose()

    logger.info("✅ Shutdown completato. Risorse rilasciate.")
    logger.info("Bye bye! 👋")


def create_app() -> FastAPI:
    """
    Inizializza e configura l'istanza FastAPI.
    
    Configura il logging, il ciclo di vita (lifespan) e registra tutti i router dell'applicazione.
    
    Returns:
        FastAPI: L'applicazione configurata e pronta all'uso.
    """ 
    setup_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(places.router)
    app.include_router(itineraries.router)

    return app


app = create_app()