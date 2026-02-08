from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
"""
Configurazione del motore del database e della fabbrica di sessioni.
Utilizza le impostazioni globali per stabilire la connessione.
Pattern standard in team.
""" # noqa: E501 (ignorare la lunghezza della riga)

engine = create_engine(settings.database_url, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
