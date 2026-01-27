from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.db.session import SessionLocal
from app.models.place import BestTime, Place, PlaceType

router = APIRouter(tags=["places"])


def get_db() -> Session:
    """
    Dependency FastAPI: apre una sessione DB per-request e la chiude a fine richiesta.
    Pattern standard in team.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_place_api(row: PlaceDB) -> Place:
    """
    Converte il modello DB (SQLAlchemy) nel modello API (Pydantic) usato come response_model.
    """
    tags = [t for t in (row.tags or "").split(",") if t]  # "a,b,c" -> ["a","b","c"]
    return Place.model_validate(
        {
            "id": row.id,
            "name": row.name,
            "area": row.area,
            "type": row.type,
            "duration_hours": row.duration_hours,
            "best_time": row.best_time,
            "price_level": row.price_level,
            "tags": tags,
        }
    )


@router.get("/places", response_model=list[Place])
def list_places(
    area: Optional[str] = Query(default=None, description="Filter by area (e.g. Ubud)"),
    type: Optional[PlaceType] = Query(default=None, description="Filter by place type"),
    best_time: Optional[BestTime] = Query(default=None, description="Best time of day"),
    max_duration_hours: Optional[int] = Query(
        default=None, ge=1, le=24, description="Max duration in hours"
    ),
    db: Session = Depends(get_db),
) -> list[Place]:
    stmt: Select = select(PlaceDB)

    if area:
        # Case-insensitive match “pulito”
        stmt = stmt.where(PlaceDB.area.ilike(area.strip()))

    if type:
        stmt = stmt.where(PlaceDB.type == type.value)

    if best_time:
        stmt = stmt.where(PlaceDB.best_time == best_time.value)

    if max_duration_hours is not None:
        stmt = stmt.where(PlaceDB.duration_hours <= max_duration_hours)

    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]


@router.get("/places/{place_id}", response_model=Place)
def get_place(place_id: int, db: Session = Depends(get_db)) -> Place:
    row = db.get(PlaceDB, place_id)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return to_place_api(row)
