import json
import logging
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def seed_places_if_empty(db: Session) -> None:
    exists = db.execute(select(PlaceDB.id).limit(1)).first()
    if exists:
        logger.info("Database already seeded, skipping.")
        return

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "places.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    logger.info(f"Seeding {len(raw)} places...")

    for item in raw:
        tags_str = ",".join(item.get("tags", []))

        new_place = PlaceDB(
            id=item["id"],
            name=item["name"],
            area=item["area"],
            type=item["type"],
            duration_hours=item["duration_hours"],
            best_time=item["best_time"],
            price_level=item["price_level"],
            tags=tags_str,
        )

        # Genera embedding solo se il campo esiste nel modello (pgvector disponibile)
        if hasattr(PlaceDB, "embedding"):
            description = ai_service.create_place_description(new_place)
            embedding = ai_service.get_embedding(description)
            new_place.embedding = embedding
            logger.info(f"  ✓ {new_place.name} (embedding generated)")
        else:
            logger.info(f"  ✓ {new_place.name} (no embedding — pgvector not available)")

        db.add(new_place)

    db.commit()
    logger.info("Seeding completed successfully.")