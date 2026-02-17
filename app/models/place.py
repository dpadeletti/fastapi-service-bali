from enum import Enum
from pydantic import BaseModel, Field


class PlaceType(str, Enum):
    """
    Enumerazione delle tipologie di luoghi supportate dal sistema.
    """
    beach = "beach"
    temple = "temple"
    nature = "nature"
    adventure = "adventure"
    island = "island"
    fun = "fun"


class BestTime(str, Enum):
    """
    Enumerazione dei momenti migliori della giornata per visitare un luogo.
    """
    morning = "morning"
    afternoon = "afternoon"
    sunset = "sunset"
    evening = "evening"


class PriceLevel(str, Enum):    
    """
    Enumerazione dei livelli di prezzo per un luogo di interesse.
    """
    low = "low"
    medium = "medium"
    high = "high"


class Place(BaseModel): 
    """
    Schema per la restituzione di un luogo di interesse.

    Attributes:
        id (int): ID del luogo.
        name (str): Nome del luogo.
        area (str): Area geografica del luogo.
        type (PlaceType): Tipo di luogo.
        duration_hours (int): Durata stimata in ore per visitare il luogo.
        best_time (BestTime): Ora migliore per visitare il luogo.
        price_level (PriceLevel): Livello di prezzo del luogo.
        tags (list[str]): Tag CSV separati per il luogo.
    """ # noqa: E501 (ignorare la lunghezza della riga) - Pydantic validation rules.
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=3, max_length=120)
    area: str = Field(..., min_length=3, max_length=120)
    type: PlaceType
    duration_hours: int = Field(..., ge=1, le=24)
    best_time: BestTime = Field(..., min_length=3, max_length=120)
    price_level: PriceLevel = Field(..., min_length=3, max_length=120)
    tags: list[str] = Field(default_factory=list)
