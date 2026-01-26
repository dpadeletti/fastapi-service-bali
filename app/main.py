from fastapi import FastAPI

from app.api import health, places
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name)

app.include_router(health.router)
app.include_router(places.router)
