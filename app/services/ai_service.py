import requests
from app.db.models.place import PlaceDB

class AIService:
    def __init__(self):
        # Dato che lanci l'app localmente sul Mac, usa localhost.
        # Se un giorno vorrai far girare TUTTO dentro Docker, allora userai host.docker.internal.
        self.url = "http://localhost:11434/api/embeddings"
        self.model = "nomic-embed-text"
        print(f"🤖 AI Service caricato con Ollama (Modello: {self.model})")

    def get_embedding(self, text: str) -> list[float]:
        try:
            payload = {
                "model": self.model,
                "prompt": text
            }
            # Un piccolo trucco: se localhost fallisce (perché magari sei in Docker),
            # potresti voler provare host.docker.internal, ma per ora restiamo semplici.
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"❌ Errore embedding Ollama: {e}")
            raise e

    def create_place_description(self, place: PlaceDB) -> str:
        return f"Posto: {place.name}. Area: {place.area}. Caratteristiche: {place.tags}."

ai_service = AIService()