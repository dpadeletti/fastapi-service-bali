.PHONY: help check-env db-up db-down db-logs migrate local docker docker-dev logs clean

ENV_LOCAL := .env.local
ENV_DOCKER := .env.docker

help:
	@echo ""
	@echo "Targets:"
	@echo "  make local        DB in Docker + API in locale (reload) + migrate"
	@echo "  make migrate      Alembic upgrade head su DB locale"
	@echo "  make db-up        Avvia solo Postgres (Docker)"
	@echo "  make db-down      Ferma stack (Docker)"
	@echo "  make docker       Avvia API (prod-like) + DB in Docker"
	@echo "  make docker-dev   Avvia API dev (reload) + DB in Docker"
	@echo "  make logs         Log docker compose (tutti i servizi)"
	@echo "  make db-logs      Log solo Postgres"
	@echo "  make clean        Ferma tutto e rimuove volumi"
	@echo ""

check-env:
	@test -f $(ENV_LOCAL) || (echo "Missing $(ENV_LOCAL). Create it first." && exit 1)
	@test -f $(ENV_DOCKER) || (echo "Missing $(ENV_DOCKER). Create it first." && exit 1)

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-logs:
	docker compose logs -f --tail=200 db

migrate: check-env
	@set -a; . ./$(ENV_LOCAL); set +a; alembic upgrade head

local: check-env db-up migrate
	@set -a; . ./$(ENV_LOCAL); set +a; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker: check-env
	docker compose --env-file $(ENV_DOCKER) up --build api

docker-dev: check-env
	docker compose --env-file $(ENV_DOCKER) up --build api-dev

logs:
	docker compose logs -f --tail=200

clean:
	docker compose down -v --remove-orphans