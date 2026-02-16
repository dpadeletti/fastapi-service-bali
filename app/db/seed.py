import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.services.ai_service import ai_service # Importiamo il servizio AI

def seed_places_if_empty(db: Session) -> None:
    exists = db.execute(select(PlaceDB.id).limit(1)).first()
    if exists:
        return

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "places.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    print("--- 🏝️ Inizio seeding con Embedding AI ---")

    for item in raw:
        tags_str = ",".join(item.get("tags", []))
        
        # 1. Creiamo temporaneamente l'oggetto per generare la descrizione
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

        # 2. Generiamo l'embedding tramite Gemini
        print(f"Vettorizzazione di: {new_place.name}...")
        description = ai_service.create_place_description(new_place)
        new_place.embedding = ai_service.get_embedding(description)

        db.add(new_place)

    db.commit()
    print("--- ✅ Seeding completato con successo! ---")