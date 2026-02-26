import os
from fastapi import APIRouter
from app.services.ai_service import ai_service

router = APIRouter(tags=["debug"])


@router.get("/debug/embedding")
def test_embedding():
    """Endpoint temporaneo per verificare che Bedrock Titan Embeddings funzioni."""
    text = "romantic dinner on the beach"
    embedding = ai_service.get_embedding(text)
    non_zero = sum(1 for v in embedding if v != 0.0)
    return {
        "env": ai_service.env,
        "text": text,
        "embedding_length": len(embedding),
        "non_zero_dimensions": non_zero,
        "first_5_values": embedding[:5],
        "bedrock_working": non_zero > 0,
    }
