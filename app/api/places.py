from typing import Any, Generator
import requests
import os
import boto3
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.db.models.place import PlaceDB
from app.db.session import SessionLocal
from app.models.place import BestTime, Place, PlaceType

from fastapi.responses import StreamingResponse
import json

router = APIRouter(tags=["places"])
logger = logging.getLogger(__name__)


def get_db() -> Session:
    """
    Dependency FastAPI: apre una sessione DB per-request e la chiude a fine richiesta.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_place_api(row: PlaceDB) -> Place:
    """
    Mappa i dati dal modello DB al modello API.
    Converte la stringa CSV dei tag in lista Python.
    """
    tags = [t for t in (row.tags or "").split(",") if t]
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


@router.get("/places/chat")
def chat_with_places(q: str, db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    try:
        results = search_places(q=q, limit=3, db=db)
        context_str = ""
        for place in results:
            context_str += f"- {place.name} (Area: {place.area})\n"
    except Exception as e:
        logger.error(f"Search error: {e}")
        context_str = "Nessun posto specifico trovato."

    system_instruction = (
        "Sei una guida turistica locale di Bali amichevole ed esperta. "
        "Usa il contesto fornito per rispondere."
    )

    final_prompt = f"{system_instruction}\n\nDomanda utente: {q}\n\nContesto suggerito:\n{context_str}"

    return StreamingResponse(generate(final_prompt), media_type="text/plain")


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
    """
    stmt: Select = select(PlaceDB)

    if area:
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
    q: str = Query(..., description="Ricerca testuale su nome, area e tag"),
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[Place]:
    """
    Ricerca testuale semplice (ILIKE) su name, area e tags.
    Sostituisce la ricerca semantica con pgvector (non supportato su questo RDS).
    """
    keyword = f"%{q.strip()}%"
    stmt = (
        select(PlaceDB)
        .where(
            or_(
                PlaceDB.name.ilike(keyword),
                PlaceDB.area.ilike(keyword),
                PlaceDB.tags.ilike(keyword),
            )
        )
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]


def generate(prompt: str) -> Generator[str, None, None]:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "bedrock":
        try:
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "eu-north-1"))
            model_id = "amazon.nova-lite-v1:0"

            payload = {
                "messages": [
                    {"role": "user", "content": [{"text": prompt}]}
                ],
                "inferenceConfig": {
                    "temperature": 0.7,
                    "max_new_tokens": 1000
                }
            }

            response = client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(payload)
            )

            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk_bytes = event.get("chunk", {}).get("bytes", b"")
                    if chunk_bytes:
                        parsed = json.loads(chunk_bytes)
                        text = parsed.get("contentBlockDelta", {}).get("delta", {}).get("text", "")
                        if text:
                            yield text

        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            yield f"Error calling AI provider: {str(e)}"

    else:
        try:
            with requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3", "prompt": prompt, "stream": True},
                stream=True
            ) as r:
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        try:
                            json_line = json.loads(decoded_line)
                            if "response" in json_line:
                                yield json_line["response"]
                        except ValueError:
                            continue
        except requests.exceptions.ConnectionError:
            yield "Errore: Assicurati che Ollama sia attivo in locale (ollama serve)."


@router.get("/places/{place_id}", response_model=Place)
def get_place(place_id: int, db: Session = Depends(get_db)) -> Place:
    """
    Recupera un luogo specifico dal DB tramite ID.
    """
    row = db.get(PlaceDB, place_id)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return to_place_api(row)