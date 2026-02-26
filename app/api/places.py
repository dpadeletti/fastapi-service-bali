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
from app.services.ai_service import ai_service

from fastapi.responses import StreamingResponse
import json

router = APIRouter(tags=["places"])
logger = logging.getLogger(__name__)

# Controlla se pgvector è disponibile (Aurora) o no (RDS standard / locale)
try:
    from pgvector.sqlalchemy import Vector  # noqa: F401
    _PGVECTOR = True
except ImportError:
    _PGVECTOR = False

# Synonym map: fallback per quando pgvector non è disponibile
SYNONYMS: dict[str, list[str]] = {
    "dog":       ["pet"],
    "dogs":      ["pet"],
    "cat":       ["pet"],
    "cats":      ["pet"],
    "pet":       ["pet"],
    "cafe":      ["food", "relax"],
    "caffè":     ["food", "relax"],
    "coffee":    ["coffee", "cafe"],
    "food":      ["food", "seafood"],
    "eat":       ["food", "seafood"],
    "dinner":    ["dinner", "seafood", "food"],
    "lunch":     ["food", "seafood"],
    "relax":     ["relax", "peace"],
    "swim":      ["swimming"],
    "diving":    ["diving"],
    "snorkel":   ["snorkeling"],
    "hike":      ["hiking", "trekking"],
    "trek":      ["trekking", "adventure"],
    "waterfall": ["waterfall"],
    "volcano":   ["volcano"],
    "sunrise":   ["sunrise"],
    "sunset":    ["sunset"],
    "surf":      ["surf", "surfing"],
    "temple":    ["temple", "spiritual"],
    "island":    ["island", "boat"],
    "beach":     ["beach"],
    "monkey":    ["monkeys"],
    "rice":      ["rice fields"],
    "photo":     ["photo-spot", "instagram"],
    "yoga":      ["yoga", "wellness"],
    "spa":       ["spa", "massage"],
    "wellness":  ["wellness", "healing"],
    "family":    ["family", "kids"],
    "kids":      ["kids", "family"],
    "romantic":  ["romantic", "couples"],
    "couples":   ["romantic", "couples"],
    "cheap":     ["low"],
    "budget":    ["low"],
    "luxury":    ["high", "upscale"],
    "upscale":   ["upscale", "high"],
    "adventure": ["adventure", "active"],
    "quiet":     ["peaceful", "quiet", "secluded"],
    "hidden":    ["hidden gem", "secluded"],
    "jungle":    ["jungle", "forest"],
    "lake":      ["lake"],
    "night":     ["nightlife"],
}

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "i", "you", "he", "she", "we", "they", "my", "your", "its", "this", "that",
    "with", "from", "by", "about", "some", "any", "like", "want", "enjoy",
    "nice", "good", "great", "best", "place", "places", "go", "there", "where",
    "suggestion", "suggestions", "recommend", "looking",
}


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_place_api(row: PlaceDB) -> Place:
    tags = [t for t in (row.tags or "").split(",") if t]
    return Place.model_validate({
        "id": row.id,
        "name": row.name,
        "area": row.area,
        "type": row.type,
        "duration_hours": row.duration_hours,
        "best_time": row.best_time,
        "price_level": row.price_level,
        "tags": tags,
    })


def expand_keywords(q: str) -> list[str]:
    words = q.lower().split()
    keywords: list[str] = []
    for word in words:
        clean = word.strip(".,!?;:'\"")
        if clean in STOP_WORDS or len(clean) < 3:
            continue
        keywords.append(clean)
        keywords.extend(SYNONYMS.get(clean, []))
    return list(dict.fromkeys(keywords))


@router.get("/places/chat")
def chat_with_places(
    q: str,
    lang: str = Query(default="English", description="Language for the response"),
    db: Session = Depends(get_db),
):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    try:
        results = search_places(q=q, limit=5, db=db)
        if results:
            context_str = "\n".join(
                f"- {p.name} (Area: {p.area}, Type: {p.type}, Tags: {', '.join(p.tags)})"
                for p in results
            )
        else:
            context_str = ""
    except Exception as e:
        logger.error(f"Search error: {e}")
        context_str = ""

    logger.info(f"[chat] query='{q}' lang={lang} pgvector={_PGVECTOR} context={context_str!r}")

    if context_str:
        context_block = (
            f"You have access to this list of real places in Bali from our database:\n"
            f"{context_str}\n\n"
            f"STRICT RULE: Only recommend places from the list above. "
            f"Do NOT invent, add, or mention any place not in this list."
        )
    else:
        context_block = (
            "No specific places were found in our database for this query. "
            "Answer based on your general knowledge of Bali, being clear it is general advice."
        )

    final_prompt = (
        f"You are a friendly and expert local travel guide for Bali.\n\n"
        f"LANGUAGE INSTRUCTION: You MUST reply in {lang}. This is mandatory.\n\n"
        f"{context_block}\n\n"
        f"User question: {q}\n\n"
        f"Reply in {lang}."
    )

    return StreamingResponse(generate(final_prompt), media_type="text/plain")


@router.get("/places", response_model=list[Place])
def list_places(
    area: Optional[str] = Query(default=None),
    type: Optional[PlaceType] = Query(default=None),
    best_time: Optional[BestTime] = Query(default=None),
    max_duration_hours: Optional[int] = Query(default=None, ge=1, le=24),
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
    q: str = Query(..., description="Ricerca semantica o testuale"),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[Place]:
    """
    Se pgvector è disponibile → ricerca semantica con cosine distance.
    Altrimenti → ricerca testuale ILIKE con espansione sinonimi.
    """
    if _PGVECTOR and hasattr(PlaceDB, "embedding"):
        return _semantic_search(q=q, limit=limit, db=db)
    else:
        return _keyword_search(q=q, limit=limit, db=db)


def _semantic_search(q: str, limit: int, db: Session) -> list[Place]:
    """Ricerca semantica via cosine distance su embedding pgvector."""
    query_embedding = ai_service.get_embedding(q)
    distance_col = PlaceDB.embedding.cosine_distance(query_embedding)
    stmt = (
        select(PlaceDB)
        .where(PlaceDB.embedding.is_not(None))
        .order_by(distance_col)
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]


def _keyword_search(q: str, limit: int, db: Session) -> list[Place]:
    """Ricerca testuale ILIKE con espansione sinonimi — fallback senza pgvector."""
    keywords = expand_keywords(q)
    if not keywords:
        return []
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(PlaceDB.name.ilike(pattern))
        conditions.append(PlaceDB.area.ilike(pattern))
        conditions.append(PlaceDB.tags.ilike(pattern))
    stmt = select(PlaceDB).where(or_(*conditions)).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [to_place_api(r) for r in rows]


def generate(prompt: str) -> Generator[str, None, None]:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "bedrock":
        try:
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "eu-north-1"))
            payload = {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"temperature": 0.7, "max_new_tokens": 1000}
            }
            response = client.invoke_model_with_response_stream(
                modelId="amazon.nova-lite-v1:0", body=json.dumps(payload)
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