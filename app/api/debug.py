import os
import json
import boto3
from fastapi import APIRouter

router = APIRouter(tags=["debug"])


@router.get("/debug/embedding")
def test_embedding():
    region = os.getenv("AWS_REGION", "eu-north-1")
    provider = os.getenv("LLM_PROVIDER", "ollama")

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({
                "inputText": "romantic dinner on the beach"
            })
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