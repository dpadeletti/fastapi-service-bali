from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.db.models.place import PlaceDB
from app.db.models.itinerary import ItineraryDB, ItineraryDayDB, ItineraryStopDB  
from app.models.itinerary import ItineraryCreate, ItineraryOut, DayOut, StopOut, ItineraryPatch 


router = APIRouter(tags=["itineraries"])


def get_db() -> Session:
    """
    Generatore di sessioni per il database. 
    Assicura che ogni richiesta HTTP abbia la propria connessione e che 
    venga chiusa correttamente alla fine del ciclo vita della request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_out(it: ItineraryDB) -> ItineraryOut:
    """
    Funzione di mapping/trasformazione: mapping DB -> API.
    Converte un oggetto SQLAlchemy ItineraryDB (e i suoi figli Day e Stop) 
    nel modello Pydantic ItineraryOut per la risposta API (response_model).
    """
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
    """
    Crea un nuovo itinerario nel DB.
    1. Estrae tutti i place_id dal payload e verifica la loro esistenza nel DB.
    2. Costruisce la struttura ad albero (Itinerary -> Days -> Stops).
    3. Esegue il commit e ricarica l'oggetto con 'selectinload' per includere 
       tutte le relazioni nella risposta.
    """
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
    """
    Recupera un itinerario specifico dal DB tramite ID.
    Utilizza 'selectinload' per ottimizzare il caricamento dei giorni e delle tappe 
    collegate in un'unica operazione efficiente.
    Se l'itinerario non esiste, restituisce un errore 404.
    """
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

@router.put("/itineraries/{itinerary_id}", response_model=ItineraryOut)
def replace_itinerary(
    itinerary_id: int,
    payload: ItineraryCreate,
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """
    Sostituzione completa (Idempotente) di un itinerario dal DB tramite ID.
    Pulisce la collezione 'days' esistente e la rimpiazza con i nuovi dati. 
    Il comando 'db.flush()' è cruciale per gestire correttamente l'eliminazione 
    degli orfani prima del nuovo inserimento.
    Se l'itinerario non esiste, restituisce un errore 404.
    """
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

    # Validate that all place_id exist
    place_ids = {s.place_id for day in payload.days for s in day.stops}
    if place_ids:
        existing = db.execute(select(PlaceDB.id).where(PlaceDB.id.in_(place_ids))).scalars().all()
        missing = place_ids - set(existing)
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown place_id(s): {sorted(missing)}")

    it.title = payload.title

    # Replace nested structure deterministically
    it.days.clear()
    db.flush()  # <-- IMPORTANT: applica le delete-orphan prima di inserire i nuovi days
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

    db.commit()

    it_full = (
        db.execute(
            select(ItineraryDB)
            .where(ItineraryDB.id == itinerary_id)
            .options(selectinload(ItineraryDB.days).selectinload(ItineraryDayDB.stops))
        )
        .scalars()
        .one()
    )
    return to_out(it_full)


@router.patch("/itineraries/{itinerary_id}", response_model=ItineraryOut)
def patch_itinerary(
    itinerary_id: int,
    payload: ItineraryPatch,
    db: Session = Depends(get_db),
) -> ItineraryOut:
    """
    Aggiornamento parziale dell'itinerario dal DB tramite ID.
    Attualmente permette di modificare solo il titolo se fornito nel payload, 
    mantenendo invariata la struttura dei giorni.
    Se l'itinerario non esiste, restituisce un errore 404.
    """
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

    if payload.title is not None:
        it.title = payload.title

    db.commit()

    it_full = (
        db.execute(
            select(ItineraryDB)
            .where(ItineraryDB.id == itinerary_id)
            .options(selectinload(ItineraryDB.days).selectinload(ItineraryDayDB.stops))
        )
        .scalars()
        .one()
    )
    return to_out(it_full)


@router.delete("/itineraries/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary(itinerary_id: int, db: Session = Depends(get_db)) -> None:
    """
    Elimina un itinerario dal DB tramite ID.
    Se l'itinerario non esiste, restituisce un errore 404.
    """
    it = db.get(ItineraryDB, itinerary_id)
    if not it:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    db.delete(it)
    db.commit()
    return None
