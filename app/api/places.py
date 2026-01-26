import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.place import Place, PlaceType, BestTime

router = APIRouter(tags=["places"])


@lru_cache(maxsize=1)
def load_places() -> list[Place]:
    """
    Carica i luoghi dal file JSON e li converte in modelli Pydantic.
    Usiamo lru_cache per non rileggere il file ad ogni richiesta (più efficiente).
    """
    project_root = Path(__file__).resolve().parents[2]  # .../fastapi-service-bali
    data_path = project_root / "data" / "places.json"

    if not data_path.exists():
        raise RuntimeError(f"Missing data file: {data_path}")

    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return [Place.model_validate(item) for item in raw]


@router.get("/places", response_model=list[Place])
def list_places(
    area: Optional[str] = Query(default=None, description="Filter by area (e.g. Ubud)"),
    type: Optional[PlaceType] = Query(default=None, description="Filter by place type"),
    best_time: Optional[BestTime] = Query(default=None, description="Best time of day"),
    max_duration_hours: Optional[int] = Query(default=None, ge=1, le=24, description="Max duration in hours"),
) -> list[Place]:
    places = load_places()
    results = places

    if area:
        area_lower = area.strip().lower()
        results = [p for p in results if p.area.lower() == area_lower]

    if type:
        results = [p for p in results if p.type == type]

    if best_time:
        results = [p for p in results if p.best_time == best_time]

    if max_duration_hours is not None:
        results = [p for p in results if p.duration_hours <= max_duration_hours]

    return results


@router.get("/places/{place_id}", response_model=Place)
def get_place(place_id: int) -> Place:
    places = load_places()
    for p in places:
        if p.id == place_id:
            return p
    raise HTTPException(status_code=404, detail="Place not found")
