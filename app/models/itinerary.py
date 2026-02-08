from pydantic import BaseModel, Field, model_validator


class StopCreate(BaseModel):
    """
    Schema per la creazione di una singola tappa in un itinerario.

    Attributes:
        place_id (int): ID del luogo di interesse (deve essere >= 1).
        order (int): Ordine cronologico della tappa nella giornata (deve essere >= 1).
        note (str | None): Nota testuale facoltativa (massimo 200 caratteri).
    """
    place_id: int = Field(..., ge=1)
    order: int = Field(..., ge=1)
    note: str | None = Field(default=None, max_length=200)


class DayCreate(BaseModel):
    """
    Schema per la creazione di una giornata all'interno di un itinerario.

    Attributes:
        day_number (int): Numero progressivo del giorno (deve essere >= 1).
        stops (list[StopCreate]): Elenco delle tappe previste per questo giorno.
    """
    day_number: int = Field(..., ge=1)
    stops: list[StopCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_order(self):
        """
        Verifica che all'interno dello stesso giorno non esistano tappe 
        con lo stesso numero d'ordine.
        """
        orders = [s.order for s in self.stops]
        if len(orders) != len(set(orders)):
            raise ValueError("Stop 'order' must be unique within the same day")
        return self


class ItineraryCreate(BaseModel):
    """
    Schema principale per la creazione di un nuovo itinerario completo.

    Attributes:
        title (str): Titolo dell'itinerario (da 3 a 120 caratteri).
        days (list[DayCreate]): Elenco dei giorni che compongono l'itinerario.
    """
    title: str = Field(..., min_length=3, max_length=120)
    days: list[DayCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_days(self):
        """
        Verifica che all'interno dell'itinerario non esistano giorni 
        con lo stesso numero progressivo.
        """
        day_numbers = [d.day_number for d in self.days]
        if len(day_numbers) != len(set(day_numbers)):
            raise ValueError("day_number must be unique within the itinerary")
        return self


# Response models
class StopOut(BaseModel):
    """
    Schema per la restituzione di una singola tappa in un itinerario.

    Attributes:
        id (int): ID della tappa.
        place_id (int): ID del luogo di interesse.
        order (int): Ordine cronologico della tappa nella giornata.
        note (str | None): Nota testuale facoltativa.
    """
    id: int
    place_id: int
    order: int
    note: str | None = None


class DayOut(BaseModel):    
    """
    Schema per la restituzione di una giornata all'interno di un itinerario.

    Attributes:
        id (int): ID della giornata.
        day_number (int): Numero progressivo della giornata.
        stops (list[StopOut]): Elenco delle tappe previste per questa giornata.
    """
    id: int
    day_number: int
    stops: list[StopOut] = Field(default_factory=list)


class ItineraryOut(BaseModel):
    """
    Schema per la restituzione di un itinerario completo.

    Attributes:
        id (int): ID dell'itinerario.
        title (str): Titolo dell'itinerario.
        days (list[DayOut]): Elenco dei giorni che compongono l'itinerario.
    """
    id: int
    title: str
    days: list[DayOut] = Field(default_factory=list)

class ItineraryPatch(BaseModel):
    """
    Schema per la modifica parziale di un itinerario esistente.

    Attributes:
        title (str | None): Nuovo titolo dell'itinerario (da 3 a 120 caratteri).
    """
    title: str | None = Field(default=None, min_length=3, max_length=120)
