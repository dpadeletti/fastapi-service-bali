from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class PlaceDB(Base):
    """
    Modello database per i punti di interesse (Places).
    
    Attributes:
        id (int): Identificativo univoco del luogo.
        name (str): Nome del luogo (max 120 caratteri).
        area (str): Area geografica del luogo.
        type (str): Tipo di luogo (es. 'beach', 'temple', 'nature', 'adventure', 'island').
        duration_hours (int): Durata stimata in ore per visitare il luogo.
        best_time (str): Ora migliore per visitare il luogo (es. 'morning', 'afternoon', 'evening').
        price_level (str): Livello di prezzo del luogo (es. 'low', 'medium', 'high').
        tags (str): Tag CSV separati per il luogo (es. 'tag1,tag2,tag3').
    """
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    area: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    best_time: Mapped[str] = mapped_column(String, nullable=False)
    price_level: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[str] = mapped_column(String, nullable=False, default="")

    # Aggiungi la colonna embedding (1536 dimensioni)
    # La lasciamo nullable=True per gestire i record esistenti
    embedding: Mapped[list] = mapped_column(Vector(768), nullable=True)