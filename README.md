# FastAPI Service — Bali 🌴

[![CI](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml/badge.svg)](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-316192?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Backend **production-style** costruito con FastAPI e deployato su **AWS** usando **Terraform**.

Il progetto simula un servizio reale (non un tutorial giocattolo) e copre:
- API REST
- database persistente
- migrazioni versionate
- container Docker
- deploy cloud ripetibile

![Bali cover](https://images.unsplash.com/photo-1507525428034-b723cf961d3e)
---

## 🎯 Obiettivo

Costruire un backend moderno e realistico che includa:

- FastAPI + Pydantic
- PostgreSQL
- SQLAlchemy ORM
- Alembic come unica fonte di verità dello schema
- Docker
- Deploy su AWS (ECS Fargate + ALB + RDS)
- Infrastruttura come codice (Terraform)

---

## 🧱 Stack tecnologico

- **FastAPI** — API REST
- **Pydantic** — validazione input/output
- **SQLAlchemy** — ORM
- **Alembic** — migrazioni DB
- **PostgreSQL (RDS)** — database
- **Docker** — containerizzazione
- **AWS ECS Fargate** — runtime container
- **AWS ALB** — load balancer pubblico
- **AWS ECR** — registry immagini Docker
- **AWS Secrets Manager** — segreti applicativi
- **Terraform** — Infrastructure as Code
- **Pytest** — test
- **Ruff** — lint

---

## 📁 Struttura del progetto

```
.
├── app/
│   ├── api/            # Router FastAPI (health, places, itineraries)
│   ├── core/           # Config & logging
│   ├── db/             # Engine, session, models SQLAlchemy, seed
│   ├── models/         # Schemi Pydantic
│   └── main.py         # FastAPI app (lifespan)
├── alembic/            # Migrazioni DB
├── scripts/            # Script one-off (seed DB)
├── tests/              # Test Pytest
├── infra/              # Terraform (AWS infrastructure)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🧩 Funzionalità

### Health
- `GET /health`

### Places
- `GET /places`
- `GET /places/{id}`
- Filtri (es. area)
- Seed dati idempotente

### Itineraries (CRUD)
- `POST /itineraries`
- `GET /itineraries/{id}`
- `PUT /itineraries/{id}`
- `PATCH /itineraries/{id}`
- `DELETE /itineraries/{id}`

✔ Validazione `place_id`  
✔ Relazioni: itineraries → days → stops  
✔ Test completi

---

## 🗄 Database & Migrazioni

- PostgreSQL come DB principale
- **Alembic è l’unica fonte di verità dello schema**
- `Base.metadata.create_all()` **disabilitato su Postgres**
- Usato solo per SQLite locale (opzionale)

Migrazioni:
```bash
alembic upgrade head
```

---

## ⚙️ Configurazione environment

Il progetto supporta **due modalità di sviluppo** distinte:

### `.env.local` — sviluppo locale (API senza Docker)
Usato quando l’API gira sul host con `uvicorn`.

```env
DATABASE_URL=postgresql+psycopg://bali:bali@localhost:5432/bali
```
---

## 🧪 Sviluppo locale vs Docker

Il progetto può essere eseguito in **due modalità ufficiali**.

---

### ▶️ Modalità LOCAL (API senza Docker)

- Database in Docker
- API avviata in locale con hot-reload
- Ideale per sviluppo e debug

```bash
make local

---

## 🧰 Makefile

Il progetto include un `Makefile` per standardizzare i comandi di sviluppo.

Comandi principali:

```bash
make local        # DB in Docker + API locale (reload)
make docker-dev   # API + DB in Docker (reload)
make docker       # API + DB in Docker (prod-like)
make clean        # Stop container e rimozione volumi

---

## ☁️ Deploy su AWS (Terraform)

L’infrastruttura è definita in `infra/` e include:

- VPC
- Subnet pubbliche
- Application Load Balancer
- ECS Fargate (service + task definition)
- ECR
- RDS PostgreSQL
- Secrets Manager
- CloudWatch Logs

### Provisioning infrastruttura

```bash
cd infra
terraform init
terraform apply
```

Output principali:
- `alb_dns_name`
- `ecr_repo_url`

---

## 🚀 Continuous Delivery (GitHub Actions + OIDC)

Il deploy è **manuale** (workflow_dispatch) per evitare costi AWS non necessari.

- GitHub Actions assume un IAM Role via OIDC
- Build immagine Docker
- Tag immutabile = git SHA
- Push su ECR
- Deploy automatico su ECS

✔ Nessuna AWS access key
✔ Nessun secret statico
✔ Terraform non coinvolto nel CD (solo lifecycle app)

---


## 🧾 Versioning & Observability

- Ogni immagine Docker è taggata con il git SHA
- Lo SHA viene loggato allo startup dell’app
- I log sono disponibili in CloudWatch Logs

Esempio:
```bash
🚀 API startup (git_sha=3a9f2c1e...)
```
--- 
## 📦 Build & Push immagine su ECR

```bash
AWS_REGION=eu-north-1
ECR_URL="<ecr_repo_url>"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$(echo $ECR_URL | cut -d/ -f1)"

docker build -t bali-api:latest .
docker tag bali-api:latest "$ECR_URL:latest"
docker push "$ECR_URL:latest"
```

Poi forzare il redeploy del service ECS.

---

## 🛠 One-off task ECS (migrazioni / seed)

Usate per operazioni amministrative in produzione.

### Migrazioni
```bash
alembic upgrade head
```

### Seed dati
```bash
sh -lc "PYTHONPATH=/app python /app/scripts/seed_db.py"
```

---

## 🔍 Verifica

```bash
curl http://<alb_dns_name>/health
curl http://<alb_dns_name>/places
```

---

## 🧠 Concetti chiave

- **No `create_all()` in produzione**
- **Alembic gestisce lo schema**
- **One-off ECS tasks** per job amministrativi
- **Terraform come contratto dell’infrastruttura**
- **Container immutabili**
- **OIDC al posto di access key**

---

## 📜 Licenza

MIT
