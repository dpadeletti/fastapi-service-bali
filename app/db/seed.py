import json
import logging
import sys
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def seed_places_if_empty(db: Session, force: bool = False) -> None:
    if not force:
        exists = db.execute(select(PlaceDB.id).limit(1)).first()
        if exists:
            logger.info("Database already seeded, skipping.")
            return

    if force:
        logger.info("Force mode: truncating places table...")
        db.execute(text("TRUNCATE TABLE places RESTART IDENTITY CASCADE"))
        db.commit()

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "places.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    logger.info(f"Seeding {len(raw)} places... (env={ai_service.env}, provider check)")

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

        if hasattr(PlaceDB, "embedding"):
            description = ai_service.create_place_description(new_place)
            embedding = ai_service.get_embedding(description)
            non_zero = sum(1 for v in embedding if v != 0.0)
            new_place.embedding = embedding
            logger.info(f"  ✓ {new_place.name} (non-zero dims: {non_zero}/768)")
        else:
            logger.info(f"  ✓ {new_place.name} (no embedding)")

        db.add(new_place)

    db.commit()
    logger.info("Seeding completed successfully.")


if __name__ == "__main__":
    import os
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    logger.info(f"seed_db.py starting — ENVIRONMENT={os.getenv('ENVIRONMENT')} LLM_PROVIDER={os.getenv('LLM_PROVIDER')}")

    from app.db.session import SessionLocal
    force = "--force" in sys.argv
    db = SessionLocal()
    try:
        seed_places_if_empty(db, force=force)
    finally:
        db.close()