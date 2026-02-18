import os
import json
import requests
import boto3 
from app.db.models.place import PlaceDB

class AIService:
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "development")
        self.model_ollama = "nomic-embed-text"
        self.model_bedrock = "amazon.nova-lite-v1:0" # Nova 2 Lite a Stoccolma
        
        # Inizializziamo il client AWS solo se siamo in produzione
        if self.env == "prod":
            self.bedrock = boto3.client("bedrock-runtime", region_name="eu-north-1")

    def get_embedding(self, text: str) -> list[float]:
        if os.getenv("TESTING") == "true":
            return [0.0] * 768
            
        # Per ora manteniamo Ollama per gli embedding anche in prod o 
        # restituiamo un vettore neutro se Ollama non risponde su AWS.
        try:
            url = "http://localhost:11434/api/embeddings"
            payload = {"model": self.model_ollama, "prompt": text}
            response = requests.post(url, json=payload, timeout=2)
            return response.json()["embedding"]
        except:
            return [0.0] * 768 # Fallback di sicurezza

    def generate_chat_response(self, prompt: str):
        if self.env == "prod":
            # --- LOGICA AWS BEDROCK (Nova 2 Lite) ---
            body = json.dumps({
                "inferenceConfig": {"max_new_tokens": 512, "temperature": 0.7},
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            })
            
            response = self.bedrock.invoke_model(
                modelId=self.model_bedrock,
                body=body
            )
            
            response_body = json.loads(response.get("body").read())
            return response_body["output"]["message"]["content"][0]["text"]
        else:
            # --- LOGICA OLLAMA (Il tuo fidato compagno locale) ---
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3", "prompt": prompt, "stream": False}
                )
                return response.json().get("response")
            except Exception as e:
                return f"Errore locale: Assicurati che Ollama sia attivo! ({e})"

    def create_place_description(self, place: PlaceDB) -> str:
        """
        Crea una descrizione testuale ricca per generare un embedding preciso.
        """
        return (
            f"Place: {place.name}. Type: {place.type}. "
            f"Located in {place.area}. Best visited in the {place.best_time}. "
            f"Tags and characteristics: {place.tags}."
        )

ai_service = AIService()