# Bali Trip Planner API

API FastAPI per gestire una lista di luoghi/attività a Bali e costruire basi per un itinerario.

## Requisiti
- Python 3.11+ (consigliato)
- (Opzionale) virtual environment

## Setup (locale)
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt

## Struttura del folder
fastapi-service/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   └── __init__.py
│
├── tests/
│   └── test_health.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
