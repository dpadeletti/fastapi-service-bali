from app.db.session import SessionLocal
from app.db.seed import seed_places_if_empty


def main() -> None: 
    """
    Script per il seeding del database con i dati iniziali dei luoghi di interesse.
    """
    db = SessionLocal()
    try:
        seed_places_if_empty(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
