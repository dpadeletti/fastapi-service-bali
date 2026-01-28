from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.db.models.place import PlaceDB
from app.db.models.itinerary import ItineraryDB, ItineraryDayDB, ItineraryStopDB
from app.models.itinerary import ItineraryCreate, ItineraryOut, DayOut, StopOut


router = APIRouter(tags=["itineraries"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_out(it: ItineraryDB) -> ItineraryOut:
    return ItineraryOut(
        id=it.id,
        title=it.title,
        days=[
            DayOut(
                id=d.id,
                day_number=d.day_number,
                stops=[
                    StopOut(id=s.id, place_id=s.place_id, order=s.order, note=s.note)
                    for s in d.stops
                ],
            )
            for d in it.days
        ],
    )


@router.post("/itineraries", response_model=ItineraryOut, status_code=status.HTTP_201_CREATED)
def create_itinerary(payload: ItineraryCreate, db: Session = Depends(get_db)) -> ItineraryOut:
    # Validate that all place_id exist
    place_ids = {s.place_id for day in payload.days for s in day.stops}
    if place_ids:
        existing = db.execute(select(PlaceDB.id).where(PlaceDB.id.in_(place_ids))).scalars().all()
        missing = place_ids - set(existing)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown place_id(s): {sorted(missing)}")

    it = ItineraryDB(title=payload.title)

    for day in payload.days:
        day_db = ItineraryDayDB(day_number=day.day_number)
        for stop in day.stops:
            day_db.stops.append(
                ItineraryStopDB(
                    place_id=stop.place_id,
                    order=stop.order,
                    note=stop.note,
                )
            )
        it.days.append(day_db)

    db.add(it)
    db.commit()
    db.refresh(it)

    # Reload with relationships so response is complete + ordered
    it_full = (
        db.execute(
            select(ItineraryDB)
            .where(ItineraryDB.id == it.id)
            .options(selectinload(ItineraryDB.days).selectinload(ItineraryDayDB.stops))
        )
        .scalars()
        .one()
    )
    return to_out(it_full)


@router.get("/itineraries/{itinerary_id}", response_model=ItineraryOut)
def get_itinerary(itinerary_id: int, db: Session = Depends(get_db)) -> ItineraryOut:
    it = (
        db.execute(
            select(ItineraryDB)
            .where(ItineraryDB.id == itinerary_id)
            .options(selectinload(ItineraryDB.days).selectinload(ItineraryDayDB.stops))
        )
        .scalars()
        .first()
    )
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return to_out(it)
