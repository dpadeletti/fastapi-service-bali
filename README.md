# 🌴 Bali Trip Planner API

Un servizio **FastAPI** pensato come progetto *portfolio-level* per dimostrare buone pratiche di **backend development, DevOps e CI/CD**.

L’API espone una mini base dati di luoghi e attività a **Bali**, con filtri e test automatici, ed è completamente **dockerizzata** e **integrata con GitHub Actions**.

![Bali cover](https://images.unsplash.com/photo-1507525428034-b723cf961d3e)

---

## ✨ Feature principali

* 🚀 FastAPI con struttura production-ready
* 📍 Endpoint `/places` con filtri (area, tipo, durata, best time)
* ❤️ Healthcheck `/health`
* 🧪 Test automatici con pytest
* 🐳 Docker & docker-compose (dev + prod-like)
* 🔁 CI con GitHub Actions (lint + test + Docker build)

---

## 🧱 Architettura (high level)

* **API**: FastAPI
* **Config**: `.env` + Pydantic Settings
* **Data source**: file JSON (facilmente sostituibile con DB)
* **CI**: GitHub Actions
* **Container**: Docker

---

## 📁 Struttura del progetto

```text
fastapi-service-bali/
│
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   └── places.py
│   ├── models/
│   │   └── place.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   └── __init__.py
│
├── data/
│   └── places.json
│
├── tests/
│   ├── test_health.py
│   └── test_places.py
│
├── .github/workflows/
│   └── ci.yml
│
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Requisiti

* Python **3.12+**
* Docker & Docker Compose

---

## ▶️ Avvio locale (senza Docker)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

* API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🐳 Avvio con Docker

### Dev mode (hot reload)

```bash
docker compose up --build api-dev
```

* API: [http://127.0.0.1:8001](http://127.0.0.1:8001)
* Docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### Prod-like mode

```bash
docker compose up --build api
```

* API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Test

```bash
pytest
```

---

## 🔁 Continuous Integration

La pipeline GitHub Actions esegue automaticamente:

* Lint del codice con **Ruff**
* Test con **pytest**
* Matrix Python **3.12 / 3.13**
* Build dell’immagine Docker (senza push)

Ogni push o Pull Request verso `main` deve passare la CI.

---

## 🎯 Obiettivo del progetto

Questo progetto nasce come **esercizio pratico** per:

* lavorare in modo realistico su un backend API
* simulare flussi di lavoro di team DevOps/MLOps
* creare una base solida per estensioni future (DB, auth, recommendation engine)

---

## 🚧 Prossimi sviluppi possibili

* Itinerari giornalieri (`/itinerary`)
* Persistenza dati (PostgreSQL)
* Sistema di raccomandazione (rule-based / ML)
* Deploy automatico (CD)

---

## 👤 Davide Padeletti

Progetto realizzato a scopo didattico e di crescita professionale.
