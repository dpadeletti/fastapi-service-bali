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
    """
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=3, max_length=120)
    area: str = Field(..., min_length=3, max_length=120)
    type: PlaceType
    duration_hours: int = Field(..., ge=1, le=24)
    best_time: BestTime
    price_level: PriceLevel
    tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}