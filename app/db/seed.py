import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB

def seed_places_if_empty(db: Session) -> None:
    """
    Popola il database con i dati iniziali dei luoghi se la tabella è vuota.

    Args:
        db (Session): La sessione attiva del database.

    Note:
        Legge i dati da un file JSON e converte i tag da lista a stringa CSV per il DB.
    """
    # Se la tabella non è vuota, non fare nulla.
    exists = db.execute(select(PlaceDB.id).limit(1)).first()
    if exists:
        return
    # Legge i dati da un file JSON e converte i tag da lista a stringa CSV per il DB.
    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "places.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    # Aggiunge i luoghi al database.
    for item in raw:
        tags = item.get("tags", [])
        db.add(
            PlaceDB(
                id=item["id"],
                name=item["name"],
                area=item["area"],
                type=item["type"],
                duration_hours=item["duration_hours"],
                best_time=item["best_time"],
                price_level=item["price_level"],
                tags=",".join(tags),
            )
        )

    # Committa le modifiche al database.
    db.commit()
