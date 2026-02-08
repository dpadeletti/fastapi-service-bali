from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ItineraryDB(Base):
    """
    Rappresenta la tabella principale degli itinerari nel database.
    
    Attributes:
        id (int): Identificativo univoco dell'itinerario.
        title (str): Titolo dell'itinerario (max 120 caratteri).
        days (list): Relazione con i giorni associati, ordinati per numero del giorno.
    """
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)

    days: Mapped[list["ItineraryDayDB"]] = relationship(
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryDayDB.day_number",
    )


class ItineraryDayDB(Base):
    """
    Modello per un singolo giorno all'interno di un itinerario.    
    
    Attributes:
        id (int): Identificativo univoco del giorno.
        itinerary_id (int): Identificativo dell'itinerario a cui il giorno appartiene.
        day_number (int): Numero del giorno (1-7).
        itinerary (ItineraryDB): Relazione con l'itinerario a cui il giorno appartiene.
        stops (list): Relazione con le tappe associate, ordinate per ordine.
    """
    __tablename__ = "itinerary_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)

    itinerary: Mapped[ItineraryDB] = relationship(back_populates="days")

    stops: Mapped[list["ItineraryStopDB"]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="ItineraryStopDB.order",
    )

    __table_args__ = (
        UniqueConstraint("itinerary_id", "day_number", name="uq_itinerary_day"),
    )


class ItineraryStopDB(Base):
    """
    Rappresenta una singola tappa presso un luogo specifico in un determinato giorno.    
    
    Attributes:
        id (int): Identificativo univoco della tappa.
        day_id (int): Identificativo del giorno a cui la tappa appartiene.
        place_id (int): Identificativo del luogo a cui la tappa si riferisce.
        order (int): Ordine della tappa all'interno del giorno.
        note (str): Note aggiuntive sulla tappa.
        day (ItineraryDayDB): Relazione con il giorno a cui la tappa appartiene.
    """
    __tablename__ = "itinerary_stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("itinerary_days.id"), nullable=False)

    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    day: Mapped[ItineraryDayDB] = relationship(back_populates="stops")

    __table_args__ = (
        UniqueConstraint("day_id", "order", name="uq_day_stop_order"),
    )
