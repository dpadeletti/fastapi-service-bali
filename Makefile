.PHONY: help check-env db-up db-wait db-down db-logs migrate local docker docker-dev logs pg-stop pg-rm clean

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

db-wait:
	@echo "Waiting for Postgres healthcheck..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do \
	  status=$$(docker inspect -f '{{.State.Health.Status}}' bali-db 2>/dev/null || echo starting); \
	  if [ "$$status" = "healthy" ]; then echo "Postgres is healthy"; exit 0; fi; \
	  sleep 1; \
	done; \
	echo "Postgres not healthy. Showing db logs:"; \
	docker compose logs --tail=200 db; \
	exit 1

db-down:
	docker compose down

db-logs:
	docker compose logs -f --tail=200 db

migrate: check-env db-wait
	@set -a; . ./$(ENV_LOCAL); set +a; alembic upgrade head

local: check-env db-up migrate
	@set -a; . ./$(ENV_LOCAL); set +a; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker: check-env
	docker compose --env-file $(ENV_DOCKER) up --build api

docker-dev: check-env
	docker compose --env-file $(ENV_DOCKER) up --build api-dev

logs:
	docker compose logs -f --tail=200

pg-stop:
	- docker stop pg 2>/dev/null || true

pg-rm:
	- docker rm pg 2>/dev/null || true

clean: pg-stop pg-rm
	docker compose down -v --remove-orphans