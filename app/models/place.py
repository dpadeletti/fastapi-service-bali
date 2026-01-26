from enum import Enum
from pydantic import BaseModel, Field


class PlaceType(str, Enum):
    beach = "beach"
    temple = "temple"
    nature = "nature"
    adventure = "adventure"
    island = "island"


class BestTime(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    sunset = "sunset"
    evening = "evening"


class PriceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Place(BaseModel):
    id: int = Field(..., ge=1)
    name: str
    area: str
    type: PlaceType
    duration_hours: int = Field(..., ge=1, le=24)
    best_time: BestTime
    price_level: PriceLevel
    tags: list[str] = Field(default_factory=list)

