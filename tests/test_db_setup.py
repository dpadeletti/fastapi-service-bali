from sqlalchemy import inspect
from app.db.session import engine

def test_tables_existence():
    """
    Verifica che tutte le tabelle necessarie siano state create nel DB.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Tabelle che DEVONO esserci se l'import nel main.py funziona
    expected_tables = ["places", "itineraries", "itinerary_days", "itinerary_stops"]
    
    for table in expected_tables:
        assert table in tables, f"La tabella {table} non è stata creata!"