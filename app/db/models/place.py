from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

try:
    from pgvector.sqlalchemy import Vector
    _pgvector_available = True
except ImportError:
    _pgvector_available = False


class PlaceDB(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    area: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    best_time: Mapped[str] = mapped_column(String, nullable=False)
    price_level: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[str] = mapped_column(String, nullable=False, default="")

    if _pgvector_available:
        embedding: Mapped[Vector] = mapped_column(Vector(1024), nullable=True)