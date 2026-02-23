# FastAPI Service — Bali 🌴

[![CI](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml/badge.svg)](https://github.com/dpadeletti/fastapi-service-bali/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-316192?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-ECS%20%2B%20RDS%20%2B%20Bedrock-FF9900?logo=amazonaws&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Backend **production-style** costruito con FastAPI e deployato su **AWS** usando **Terraform**.

Il progetto copre l'intero ciclo di vita di un servizio reale: API REST, AI generativa in streaming, database persistente, migrazioni versionate, container immutabili e deploy cloud ripetibile.

![Bali cover](https://images.unsplash.com/photo-1507525428034-b723cf961d3e)

---

## 🎯 Obiettivo

Costruire un backend moderno e realistico che includa:

- FastAPI + Pydantic
- PostgreSQL + SQLAlchemy ORM + Alembic
- AI generativa in streaming (AWS Bedrock Nova Lite)
- Chat turistica con contesto dal DB (RAG semplificato)
- Docker + AWS ECS Fargate + ALB + RDS
- Infrastruttura come codice (Terraform)
- CI/CD via GitHub Actions + OIDC (nessuna access key statica)

---

## 🧱 Stack tecnologico

| Layer | Tecnologia |
|-------|-----------|
| API | FastAPI + Pydantic |
| ORM | SQLAlchemy |
| Migrazioni | Alembic |
| Database | PostgreSQL (AWS RDS) |
| AI | AWS Bedrock — Amazon Nova Lite (`amazon.nova-lite-v1:0`) |
| AI locale | Ollama + Llama3 |
| Container | Docker |
| Runtime | AWS ECS Fargate |
| Load Balancer | AWS ALB |
| Registry | AWS ECR |
| Segreti | AWS Secrets Manager |
| IaC | Terraform |
| CI/CD | GitHub Actions + OIDC |
| Test | Pytest |
| Lint | Ruff |

---

## 📁 Struttura del progetto

```
.
├── app/
│   ├── api/                  # Router FastAPI
│   │   ├── health.py         # GET /health
│   │   ├── places.py         # GET /places, /places/chat, /places/search
│   │   └── itineraries.py    # CRUD itinerari
│   ├── core/                 # Config & logging
│   ├── db/
│   │   ├── models/           # Modelli SQLAlchemy (PlaceDB, ItineraryDB…)
│   │   ├── session.py        # Engine + SessionLocal
│   │   └── seed.py           # Seed idempotente (21 posti Bali)
│   ├── models/               # Schemi Pydantic (Place, Itinerary…)
│   ├── services/
│   │   └── ai_service.py     # AIService (Bedrock / Ollama)
│   └── main.py               # FastAPI app + lifespan
├── alembic/                  # Migrazioni DB versionate
├── data/
│   └── places.json           # Dataset 21 luoghi Bali
├── static/
│   └── index.html            # UI chatbot (luxury resort theme)
├── scripts/                  # Script one-off (seed DB)
├── tests/                    # Test Pytest
├── infra/                    # Terraform (AWS infrastructure)
│   ├── alb_ecs.tf
│   ├── iam_ecs.tf
│   ├── network.tf
│   ├── rds_secrets.tf
│   └── …
├── .github/
│   └── workflows/
│       ├── ci.yml            # Test + lint su ogni PR
│       └── deploy.yml        # Deploy manuale su ECS
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🧩 Funzionalità

### Health
- `GET /health` — health check per ALB

### Places
- `GET /places` — lista con filtri (area, type, best_time, max_duration_hours)
- `GET /places/{id}` — dettaglio singolo posto
- `GET /places/search?q=` — ricerca testuale con espansione sinonimi
- `GET /places/chat?q=&lang=` — chat AI in streaming con contesto dal DB

### Itineraries (CRUD)
- `POST /itineraries`
- `GET /itineraries/{id}`
- `PUT /itineraries/{id}`
- `PATCH /itineraries/{id}`
- `DELETE /itineraries/{id}`

✔ Validazione `place_id`
✔ Relazioni: itineraries → days → stops
✔ Test completi

### Chat AI
- Streaming in tempo reale via Server-Sent Events
- Contesto RAG: cerca i posti rilevanti nel DB prima di chiamare il modello
- Ricerca con espansione sinonimi (es. "dog" → "pet", "cafe" → "food, relax")
- Filtro stop words per evitare falsi match (es. "in" → "Kintamani")
- Lingua automatica: il browser rileva la lingua e la passa al modello
- Il modello risponde **solo** con i posti presenti nel DB

---

## 🗄 Database & Migrazioni

- PostgreSQL come DB principale
- **Alembic è l'unica fonte di verità dello schema**
- `Base.metadata.create_all()` disabilitato su Postgres (usato solo per SQLite locale)
- Seed idempotente: 21 luoghi Bali con area, type, best_time, price_level, tags

```bash
alembic upgrade head
```

---

## 🤖 AI — AWS Bedrock Nova Lite

La chat usa `amazon.nova-lite-v1:0` in modalità streaming via `invoke_model_with_response_stream`.

Il parsing corretto dei chunk:
```python
chunk_bytes = event.get("chunk", {}).get("bytes", b"")
parsed = json.loads(chunk_bytes)
text = parsed.get("contentBlockDelta", {}).get("delta", {}).get("text", "")
```

In locale il fallback è **Ollama + Llama3** (basta avere `ollama serve` attivo).

La variabile `LLM_PROVIDER=bedrock` nella Task Definition ECS controlla quale provider usare.

---

## ⚙️ Configurazione environment

### `.env.local` — sviluppo locale

```env
DATABASE_URL=postgresql+psycopg://bali:bali@localhost:5432/bali
```

### Variabili ECS (Task Definition)

| Variabile | Valore |
|-----------|--------|
| `LLM_PROVIDER` | `bedrock` |
| `AWS_REGION` | `eu-north-1` |
| `ENVIRONMENT` | `prod` |
| `DATABASE_URL` | da AWS Secrets Manager |

---

## 🧪 Sviluppo locale

```bash
make local        # DB in Docker + API locale con hot-reload
make docker-dev   # API + DB in Docker con hot-reload
make docker       # API + DB in Docker (prod-like)
make clean        # Stop container e rimozione volumi
```

---

## ☁️ Architettura AWS

```
Internet
   │
   ▼
ALB (bali-dev-alb) — DNS fisso
   │  health check: GET /health
   ▼
ECS Fargate (bali-dev-api)
   │                    │
   ▼                    ▼
RDS PostgreSQL     AWS Bedrock
(places, itiner.)  Nova Lite
   ▲
   │
Secrets Manager
(DATABASE_URL)
```

L'infrastruttura è definita in `infra/` e include VPC, subnet pubbliche, ALB, ECS, ECR, RDS, Secrets Manager, CloudWatch Logs, IAM roles.

```bash
cd infra
terraform init
terraform apply
```

Output principali: `alb_dns_name`, `ecr_repo_url`

---

## 🚀 Continuous Delivery (GitHub Actions + OIDC)

Il deploy è **manuale** (`workflow_dispatch`) per evitare costi AWS non necessari.

```
Push → GitHub Actions
  1. Guardrail: richiede "DEPLOY" come conferma
  2. Pre-check: verifica cluster e service ECS attivi
  3. Build + push immagine (tag = git SHA)
  4. Registra nuova Task Definition
  5. Lancia one-off task → alembic upgrade head + seed
  6. Attende completamento migrazioni (aws ecs wait tasks-stopped)
  7. Verifica exit code — fallisce il deploy se le migrazioni falliscono
  8. Deploy rolling update con wait-for-service-stability
```

✔ Nessuna AWS access key statica
✔ OIDC: GitHub assume IAM Role temporaneo
✔ Tag immutabili (git SHA)
✔ Zero downtime grazie al rolling update ALB

---

## 🧾 Versioning & Observability

- Ogni immagine Docker è taggata con il git SHA
- Lo SHA viene loggato allo startup:
```
🚀 API startup (git_sha=3a9f2c1e...)
```
- Log disponibili in CloudWatch: `/ecs/bali-dev-api`
- Il contesto DB passato al modello AI è loggato a livello INFO per debug

```bash
aws logs tail /ecs/bali-dev-api --region eu-north-1 --follow
```

---

## 🛠 One-off task ECS

```bash
# Migrazioni
aws ecs run-task --cluster bali-dev-cluster \
  --task-definition bali-dev-api --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"api","command":["sh","-c","alembic upgrade head"]}]}'

# Seed manuale
aws ecs run-task --cluster bali-dev-cluster \
  --task-definition bali-dev-api --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"api","command":["sh","-c","PYTHONPATH=. python scripts/seed_db.py"]}]}'
```

---

## 🔍 Verifica

```bash
curl http://<alb_dns_name>/health
curl http://<alb_dns_name>/places
curl "http://<alb_dns_name>/places/chat?q=surf+spots&lang=English"
```

---

## 💰 Spegnere tutto per risparmiare

```bash
# Stop container (RDS continua a costare)
aws ecs update-service --cluster bali-dev-cluster --service bali-dev-api --desired-count 0 --region eu-north-1

# Riavvio
aws ecs update-service --cluster bali-dev-cluster --service bali-dev-api --desired-count 1 --region eu-north-1
```

---

## 🧠 Concetti chiave

- **No `create_all()` in produzione** — Alembic gestisce lo schema
- **One-off ECS tasks** per migrazioni e seed in produzione
- **Terraform come contratto dell'infrastruttura**
- **Container immutabili** — tag = git SHA
- **OIDC al posto di access key** — nessun secret statico
- **RAG semplificato** — ricerca DB → contesto → modello AI
- **Stop words + sinonimi** — ricerca testuale robusta senza pgvector

---

## 📜 Licenza

MIT