import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "development")
        self.aws_region = os.getenv("AWS_REGION", "eu-north-1")
        self.model_bedrock = "amazon.nova-lite-v1:0"
        self.embedding_model = "amazon.titan-embed-text-v2:0"

        if self.env == "prod":
            self.bedrock = boto3.client("bedrock-runtime", region_name=self.aws_region)

    def get_embedding(self, text: str) -> list[float]:
        """
        Genera un embedding vettoriale (768 dimensioni) per il testo dato.
        - In produzione: AWS Bedrock Titan Embeddings v2
        - In locale: vettore neutro (richiede pgvector e Ollama, skip per ora)
        - In test: vettore zero
        """
        if os.getenv("TESTING") == "true":
            return [0.0] * 768

        if self.env == "prod":
            try:
                response = self.bedrock.invoke_model(
                    modelId=self.embedding_model,
                    body=json.dumps({
                        "inputText": text,
                        "dimensions": 768,
                        "normalize": True
                    })
                )
                body = json.loads(response["body"].read())
                return body["embedding"]
            except Exception as e:
                logger.error(f"Bedrock embedding error: {e}")
                return [0.0] * 768
        else:
            # Locale: vettore neutro — il seed locale non genera embedding reali
            # Per embedding locali reali: installare Ollama + nomic-embed-text
            return [0.0] * 768

    def create_place_description(self, place) -> str:
        """
        Crea una descrizione testuale ricca per generare un embedding preciso.
        Più ricca è la descrizione, più accurata è la ricerca semantica.
        """
        return (
            f"{place.name} is a {place.type} located in {place.area}, Bali. "
            f"Best visited in the {place.best_time}. "
            f"Price level: {place.price_level}. "
            f"Duration: approximately {place.duration_hours} hours. "
            f"Key features and activities: {place.tags.replace(',', ', ')}."
        )

    def generate_chat_response(self, prompt: str) -> str:
        """Risposta non-streaming — usata per testing o fallback."""
        if self.env == "prod":
            body = json.dumps({
                "inferenceConfig": {"max_new_tokens": 512, "temperature": 0.7},
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            })
            response = self.bedrock.invoke_model(
                modelId=self.model_bedrock, body=body
            )
            response_body = json.loads(response.get("body").read())
            return response_body["output"]["message"]["content"][0]["text"]
        else:
            return "Risposta locale non disponibile — usa make local con Ollama."


ai_service = AIService()