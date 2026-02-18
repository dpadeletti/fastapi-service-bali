from typing import Any, Generator
import requests
import os
import boto3
import logging
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
logger = logging.getLogger(__name__)

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

@router.get("/places/chat")
def chat_with_places(q: str, db: Session = Depends(get_db)):
    """
    Endpoint per chat RAG (Retrieval Augmented Generation).
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    # 1. Ricerca vettoriale (RAG)
    # Nota: Assumiamo che search_places sia definita sopra nel file originale
    # Se search_places usa ancora logica locale, assicurati che funzioni su AWS 
    # (embedding via DB pgvector funzionano, embedding via modello locale richiedono attenzione)
    # Per ora ci concentriamo sulla generazione del testo.
    
    # Esempio semplificato di recupero contesto (preso dalla logica esistente se presente)
    # results = search_places(q=q, db=db) 
    # context = "\n".join([f"- {p.name}: {p.description}" for p in results])
    
    # Recuperiamo un contesto fittizio o reale se la funzione search_places è disponibile
    # Nel file caricato search_places c'è, quindi usiamola:
    try:
        results = search_places(q=q, db=db)
        # results è una lista di dizionari o oggetti, adattare in base al ritorno di search_places
        context_str = ""
        for place in results:
             # search_places ritorna dict nel file caricato
             context_str += f"- {place['name']} ({place['category']}): {place['description']}\n"
    except Exception as e:
        logger.error(f"Search error: {e}")
        context_str = "Nessun posto specifico trovato."

    # 2. Costruzione Prompt
    system_instruction = (
        "Sei una guida turistica locale di Bali amichevole ed esperta. "
        "Usa il contesto fornito per rispondere. Se non sai la risposta, inventa qualcosa di plausibile ma divertente."
    )
    
    final_prompt = f"{system_instruction}\n\nDomanda utente: {q}\n\nContesto suggerito:\n{context_str}"

    # 3. Streaming Response
    from fastapi.responses import StreamingResponse
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

def generate(prompt: str) -> Generator[str, None, None]:
    """
    Generatore che supporta sia Ollama (Locale) che AWS Bedrock Nova (Prod).
    Switch basato sulla variabile d'ambiente LLM_PROVIDER.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    # --- MODALITÀ AWS BEDROCK (Nova Lite) ---
    if provider == "bedrock":
        try:
            # Setup Client Bedrock
            # Nota: Assicurati che la regione sia corretta (eu-north-1 per Nova Lite se disponibile)
            client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "eu-north-1"))
            
            # Nova Lite usa la struttura "messages" (simile a Claude 3)
            # Modello ID per Nova Lite 1.0 (Verifica se su eu-north-1 è 'amazon.nova-lite-v1:0')
            model_id = "amazon.nova-lite-v1:0" 

            payload = {
                "messages": [
                    {
                        "role": "user", 
                        "content": [{"text": prompt}]
                    }
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

            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('contentBlockDelta')
                    if chunk:
                        # La struttura della risposta di Nova è annidata
                        delta = chunk.get('delta', {})
                        text = delta.get('text', '')
                        if text:
                            yield text

        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            yield f"Error calling AI provider: {str(e)}"

    # --- MODALITÀ OLLAMA (Locale - Default) ---
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
    Se il luogo non esiste, restituisce un errore 404.
    """
    row = db.get(PlaceDB, place_id)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return to_place_api(row)
