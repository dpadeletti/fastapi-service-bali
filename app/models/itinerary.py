from pydantic import BaseModel, Field, model_validator


class StopCreate(BaseModel):
    place_id: int = Field(..., ge=1)
    order: int = Field(..., ge=1)
    note: str | None = Field(default=None, max_length=200)


class DayCreate(BaseModel):
    day_number: int = Field(..., ge=1)
    stops: list[StopCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_order(self):
        orders = [s.order for s in self.stops]
        if len(orders) != len(set(orders)):
            raise ValueError("Stop 'order' must be unique within the same day")
        return self


class ItineraryCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    days: list[DayCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_days(self):
        day_numbers = [d.day_number for d in self.days]
        if len(day_numbers) != len(set(day_numbers)):
            raise ValueError("day_number must be unique within the itinerary")
        return self


# Response models
class StopOut(BaseModel):
    id: int
    place_id: int
    order: int
    note: str | None = None


class DayOut(BaseModel):
    id: int
    day_number: int
    stops: list[StopOut] = Field(default_factory=list)


class ItineraryOut(BaseModel):
    id: int
    title: str
    days: list[DayOut] = Field(default_factory=list)

class ItineraryPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
