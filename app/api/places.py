import requests
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.db.session import SessionLocal
from app.models.place import BestTime, Place, PlaceType

from app.services.ai_service import ai_service

from fastapi.responses import StreamingResponse
import json

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
    Mappa i dati dal modello DB al modello API.
    Gestisce la deserializzazione dei tag: converte la stringa CSV salvata nel DB 
    (es. 'tag1,tag2') in una lista Python pulita (es. ['tag1', 'tag2']).
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
    """
    Ricerca filtrata dei luoghi d'interesse dal DB.
    - area: Ricerca parziale case-insensitive (ILike).
    - type/best_time: Filtri esatti basati su Enum.
    - max_duration_hours: Filtro numerico (minore o uguale a).
    Restituisce una lista di oggetti Place (modello API) filtrati.
    """
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

@router.get("/places/search", response_model=list[Place])
def search_places(
    q: str = Query(..., description="Ricerca semantica"),
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[Place]:
    query_vector = ai_service.get_embedding(q)
    
    # Calcoliamo la distanza
    distance_column = PlaceDB.embedding.cosine_distance(query_vector)
    
    stmt = (
        select(PlaceDB)
        .where(distance_column < 0.4) # <--- SOGLIA: ignora tutto ciò che è troppo diverso
        .order_by(distance_column)
        .limit(limit)
    )
    
    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]

@router.get("/places/chat")
async def chat_with_concierge(
    q: str = Query(..., description="Chiedi consiglio alla guida"),
    db: Session = Depends(get_db)
):
    # 1. Ricerca Semantica (Retrieval)
    query_vector = ai_service.get_embedding(q)
    distance_column = PlaceDB.embedding.cosine_distance(query_vector)
    
    stmt = select(PlaceDB).where(distance_column < 0.6).order_by(distance_column).limit(4)
    places = db.execute(stmt).scalars().all()
    
    # 2. Preparazione contesto per l'LLM
    context = "No specific places found." if not places else "\n".join([
        f"- {p.name} ({p.area}): {p.tags}. Best time: {p.best_time}." for p in places
    ])

    prompt = f"""You are a friendly Bali Travel Guide. 
    User Question: "{q}"
    Available Database Info:
    {context}
    Instructions: Use the info above to answer. Be short and tropical. 🌴"""

    # 3. Funzione generatrice per lo streaming
    def generate():
        with requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": True},
            stream=True
        ) as r:
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    yield chunk.get("response", "")

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/places/{place_id}", response_model=Place)
def get_place(place_id: int, db: Session = Depends(get_db)) -> Place:
    """
    Recupera un luogo specifico dal DB tramite ID.
    Se il luogo non esiste, restituisce un errore 404.
    """
    row = db.get(PlaceDB, place_id)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return to_place_api(row)
