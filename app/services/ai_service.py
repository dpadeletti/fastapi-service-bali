import os
import requests
from app.db.models.place import PlaceDB

class AIService:
    def __init__(self):
        # Indirizzo per parlare con Ollama (localhost perché usi 'make local')
        self.url = "http://localhost:11434/api/embeddings"
        self.model = "nomic-embed-text"
        print(f"🤖 AI Service caricato con Ollama (Modello: {self.model})")

    def get_embedding(self, text: str) -> list[float]:
        # AGGIUNGI QUESTO CONTROLLO PER LA CI
        if os.getenv("TESTING") == "true":
            # Restituiamo un vettore di 768 zeri per far passare i test senza Ollama
            return [0.0] * 768

        try:
            payload = {
                "model": self.model,
                "prompt": text
            }
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"❌ Errore embedding Ollama: {e}")
            raise e

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