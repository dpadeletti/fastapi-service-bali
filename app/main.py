from contextlib import asynccontextmanager
import os
import logging
import json

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import health, places, itineraries
from app.core.config import settings
from app.core.logging import setup_logging

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models.place import Place  # Import diretto per il conteggio

# Import dei modelli SQLAlchemy per registrarli su Base.metadata
from app.db.models import place as _place_model  # noqa: F401
from app.db.models import itinerary as _itinerary_model  # noqa: F401

async def perform_seeding(db):
    """Logica di popolazione automatica del database."""
    logger = logging.getLogger("uvicorn.error")
    try:
        # 1. Controlla se la tabella è vuota
        count = db.query(Place).count()
        if count == 0:
            logger.info("📭 Database RDS vuoto rilevato. Avvio seeding...")
            
            # 2. Percorso del file JSON (assicurati che sia in /app/data/bali_places.json nel container)
            json_path = os.path.join("data", "bali_places.json")
            
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        new_place = Place(**item)
                        db.add(new_place)
                db.commit()
                logger.info(f"✅ Seeding completato con successo: {len(data)} posti caricati.")
            else:
                logger.error(f"❌ File di dati non trovato in: {json_path}")
        else:
            logger.info(f"📊 Database già popolato ({count} record). Salto il seeding.")
    except Exception as e:
        logger.error(f"❌ Errore critico durante il seeding: {e}")
        db.rollback()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce l'avvio e lo spegnimento dell'app su AWS."""
    git_sha = os.getenv("GIT_SHA", "unknown")
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"🚀 API startup (git_sha={git_sha})")

    # In locale con SQLite crea le tabelle, su AWS ci pensa Alembic
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    # Esecuzione del Seeding
    db = SessionLocal()
    try:
        await perform_seeding(db)
    finally:
        db.close()

    yield

    logger.info("🛑 API shutting down...")
    engine.dispose()
    logger.info("✅ Shutdown completato. Risorse rilasciate.")

def create_app() -> FastAPI:
    """Inizializza e configura l'istanza FastAPI.""" 
    setup_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(health.router)
    app.include_router(places.router)
    app.include_router(itineraries.router)

    # Importante: la cartella 'static' deve essere stata copiata nel Dockerfile
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    
    return app

app = create_app()