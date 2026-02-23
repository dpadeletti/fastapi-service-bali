from typing import Generator
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

# Synonym map: user terms → DB tag keywords
SYNONYMS: dict[str, list[str]] = {
    "dog":       ["pet"],
    "dogs":      ["pet"],
    "cat":       ["pet"],
    "cats":      ["pet"],
    "pet":       ["pet"],
    "cafe":      ["food", "relax"],
    "caffè":     ["food", "relax"],
    "coffee":    ["food", "relax"],
    "food":      ["food", "seafood"],
    "eat":       ["food", "seafood"],
    "dinner":    ["dinner", "seafood", "food"],
    "lunch":     ["food", "seafood"],
    "relax":     ["relax", "peace"],
    "swim":      ["swimming"],
    "swimming":  ["swimming"],
    "dive":      ["diving"],
    "diving":    ["diving"],
    "snorkel":   ["snorkeling"],
    "hike":      ["hiking", "trekking"],
    "hiking":    ["hiking", "trekking"],
    "trek":      ["trekking", "adventure"],
    "waterfall": ["waterfall"],
    "volcano":   ["volcano"],
    "sunrise":   ["sunrise"],
    "sunset":    ["sunset"],
    "surf":      ["surf", "surfing"],
    "surfing":   ["surfing", "surf"],
    "temple":    ["temple", "spiritual"],
    "island":    ["island", "boat"],
    "beach":     ["beach"],
    "monkey":    ["monkeys"],
    "monkeys":   ["monkeys"],
    "rice":      ["rice fields"],
    "photo":     ["photo-spot", "instagram", "views"],
    "instagram": ["instagram", "photo-spot"],
    "view":      ["views", "viewpoints"],
    "views":     ["views", "viewpoints"],
    "garden":    ["garden", "flowers"],
    "spiritual": ["spiritual", "temple"],
    "authentic": ["authentic"],
    "jungle":    ["jungle", "forest"],
    "forest":    ["forest", "jungle"],
    "lake":      ["lake"],
    "mountain":  ["mountains", "volcano"],
    "night":     ["nightlife"],
    "nightlife": ["nightlife"],
}


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_place_api(row: PlaceDB) -> Place:
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


def expand_keywords(q: str) -> list[str]:
    """
    Splits query into words and expands each with synonyms.
    Returns a flat deduplicated list of keywords to search for.
    """
    words = q.lower().split()
    keywords: list[str] = []
    for word in words:
        keywords.append(word)
        keywords.extend(SYNONYMS.get(word, []))
    return list(dict.fromkeys(keywords))  # deduplicate preserving order


@router.get("/places/chat")
def chat_with_places(
    q: str,
    lang: str = Query(default="English", description="Language for the response"),
    db: Session = Depends(get_db),
):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    try:
        results = _search_by_keywords(q=q, limit=5, db=db)
        if results:
            context_str = "\n".join(
                f"- {p.name} (Area: {p.area}, Type: {p.type}, Tags: {', '.join(p.tags)})"
                for p in results
            )
        else:
            context_str = "No specific places found in the database for this query."
    except Exception as e:
        logger.error(f"Search error: {e}")
        context_str = "No specific places found in the database for this query."

    final_prompt = (
        f"You are a friendly and expert local travel guide for Bali.\n\n"
        f"LANGUAGE INSTRUCTION: You MUST reply in {lang}. This is mandatory.\n\n"
        f"User question: {q}\n\n"
        f"Relevant places from our database:\n{context_str}\n\n"
        f"Answer the user's question using the places above when relevant. "
        f"Reply in {lang}."
    )

    return StreamingResponse(generate(final_prompt), media_type="text/plain")


def _search_by_keywords(q: str, limit: int, db: Session) -> list[Place]:
    """
    Expanded keyword search: splits the query, applies synonyms,
    and searches name + area + tags for any of the resulting keywords.
    """
    keywords = expand_keywords(q)
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(PlaceDB.name.ilike(pattern))
        conditions.append(PlaceDB.area.ilike(pattern))
        conditions.append(PlaceDB.tags.ilike(pattern))

    stmt = select(PlaceDB).where(or_(*conditions)).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]


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
    """Ricerca testuale con espansione dei sinonimi."""
    return _search_by_keywords(q=q, limit=limit, db=db)


def generate(prompt: str) -> Generator[str, None, None]:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "bedrock":
        try:
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "eu-north-1"))
            model_id = "amazon.nova-lite-v1:0"
            payload = {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"temperature": 0.7, "max_new_tokens": 1000}
            }
            response = client.invoke_model_with_response_stream(
                modelId=model_id, body=json.dumps(payload)
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
                        try:
                            json_line = json.loads(line.decode("utf-8"))
                            if "response" in json_line:
                                yield json_line["response"]
                        except ValueError:
                            continue
        except requests.exceptions.ConnectionError:
            yield "Errore: Assicurati che Ollama sia attivo in locale (ollama serve)."


@router.get("/places/{place_id}", response_model=Place)
def get_place(place_id: int, db: Session = Depends(get_db)) -> Place:
    row = db.get(PlaceDB, place_id)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return to_place_api(row)