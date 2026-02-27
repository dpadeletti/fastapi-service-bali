import os
import json
import boto3
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from app.db.session import SessionLocal
from app.db.models.place import PlaceDB

router = APIRouter(tags=["debug"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/debug/embedding")
def test_embedding():
    """Testa Bedrock Titan Embeddings direttamente."""
    region = os.getenv("AWS_REGION", "eu-north-1")
    provider = os.getenv("LLM_PROVIDER", "ollama")

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": "romantic dinner on the beach"})
        )
        body = json.loads(response["body"].read())
        embedding = body.get("embedding", [])
        non_zero = sum(1 for v in embedding if v != 0.0)
        return {
            "provider": provider,
            "region": region,
            "embedding_length": len(embedding),
            "non_zero_dimensions": non_zero,
            "first_5_values": embedding[:5],
            "bedrock_working": non_zero > 0,
            "error": None
        }
    except Exception as e:
        return {
            "provider": provider,
            "region": region,
            "bedrock_working": False,
            "error": str(e)
        }


@router.get("/debug/embedding-status")
def embedding_status(db: Session = Depends(get_db)):
    """Controlla quanti posti nel DB hanno embedding non-null."""
    total = db.execute(select(func.count()).select_from(PlaceDB)).scalar()
    with_embedding = db.execute(
        select(func.count()).select_from(PlaceDB).where(PlaceDB.embedding.is_not(None))
    ).scalar()

    # Sample di 3 posti con e senza embedding
    sample_with = db.execute(
        select(PlaceDB.name).where(PlaceDB.embedding.is_not(None)).limit(3)
    ).scalars().all()

    sample_without = db.execute(
        select(PlaceDB.name).where(PlaceDB.embedding.is_(None)).limit(3)
    ).scalars().all()

    return {
        "total_places": total,
        "with_embedding": with_embedding,
        "without_embedding": total - with_embedding,
        "embedding_coverage": f"{with_embedding}/{total}",
        "sample_with_embedding": sample_with,
        "sample_without_embedding": sample_without,
    }