# FastAPI Service — Bali 🌴

[![CI](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml/badge.svg)](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-316192?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Backend service built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**, designed as a realistic DevOps/MLOps-style project.  
The API manages **places** and **travel itineraries** for Bali, with full CRUD, database migrations, Docker, and CI.

![Bali cover](https://images.unsplash.com/photo-1507525428034-b723cf961d3e)

---

## ✨ Features

- FastAPI REST API
- CRUD for itineraries (POST / GET / PUT / PATCH / DELETE)
- Places catalog (seeded data)
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL (Dockerized)
- Docker & docker-compose
- CI with GitHub Actions
  - Ruff (lint)
  - Pytest
  - PostgreSQL service
  - Alembic migrations + DB seed
  - Python matrix (3.12 / 3.13)
- Architecture diagram in `docs/`

---

## 🏗 Architecture Diagram

![Architecture diagram](docs/architecture-diagram.png)

**Flow:** Client → FastAPI → Postgres.  
Schema changes are managed with **Alembic**.  
CI runs on **GitHub Actions** (lint + migrations + seed + tests).

---

## 🗂 Project Structure

```
.
├── app/
│   ├── api/            # FastAPI routers
│   ├── core/           # Settings & config
│   ├── db/             # DB session, models, seed
│   ├── models/         # Pydantic schemas
│   └── main.py         # FastAPI app
├── alembic/             # DB migrations
├── scripts/             # Utility scripts (e.g. seed DB for CI)
├── tests/               # Pytest suite
├── docs/                # Documentation assets (diagrams, etc.)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Running Locally (Docker)

### 1) Environment variables

Create a `.env` file:

```
DATABASE_URL=postgresql+psycopg://bali:bali@db:5432/bali
```

### 2) Start services

```
docker compose up -d db api
```

### 3) Run migrations (recommended way)

Run migrations with a one-shot container (does not start Uvicorn):

```
docker compose run --rm api alembic upgrade head
```

### 4) API available at

- Health check: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## 🧪 Running Tests

### Local

```
pytest
```

### CI

CI runs automatically on **pull requests and pushes to `main`** and includes:

- Ruff linting
- PostgreSQL service
- Alembic migrations
- Database seed
- Pytest (Python 3.12 & 3.13)

---

## 🗄 Database & Migrations

- Database schema is managed **via Alembic**.
- SQLite can be used for local experiments, but PostgreSQL is the reference DB.
- Migrations should run before starting the API in a fresh environment.

---

## 🧭 Example API Usage

### Create an itinerary

```
POST /itineraries
{
  "title": "Bali 2 days",
  "days": [
    {
      "day_number": 1,
      "stops": [{"place_id": 1, "order": 1}]
    }
  ]
}
```

### Get all places

```
GET /places
```

---

## 📌 Notes

- Designed as a **production-style backend project**, not a toy example.
- Focus on correctness, migrations, CI, and Docker workflow.
- Ready for future extensions (auth, recommendations, deployment/CD).

---

## 📜 License

MIT
