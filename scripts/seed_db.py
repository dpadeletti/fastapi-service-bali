from app.db.session import SessionLocal
from app.db.seed import seed_places_if_empty


def main() -> None:
    db = SessionLocal()
    try:
        seed_places_if_empty(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
