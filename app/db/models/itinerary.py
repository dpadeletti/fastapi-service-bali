from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ItineraryDB(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)

    days: Mapped[list["ItineraryDayDB"]] = relationship(
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryDayDB.day_number",
    )


class ItineraryDayDB(Base):
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
