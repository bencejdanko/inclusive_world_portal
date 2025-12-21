.PHONY: help up down install run runserver rundev migrate makemigrations superuser test reset celery-worker celery-beat shell dbshell collectstatic

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start backing services (Postgres, Redis, Minio)
	docker compose up -d

down: ## Stop backing services
	docker compose down

install: ## Install dependencies using uv
	uv sync

run:
	RUN_CELERY_WORKERS=true uv run --env-file .env honcho -f Procfile.dev start

migrate: ## Run database migrations
	uv run --env-file .env manage.py migrate

makemigrations: ## Create new migrations
	uv run --env-file .env manage.py makemigrations

collectstatic: ## Collect static files (required after static file changes)
	uv run --env-file .env manage.py collectstatic --noinput

superuser: ## Create Django superuser
	uv run --env-file .env manage.py createsuperuser

test: ## Run tests
	uv run --env-file .env pytest

reset: ## Destroy all data (volumes) and restart services
	docker compose down --remove-orphans
	docker volume rm inclusive_world_portal_postgres_data || true
	docker volume rm inclusive_world_portal_redis_data || true
	docker volume rm inclusive_world_portal_minio_data || true
	$(MAKE) up

celery-worker: ## Run Celery worker locally
	uv run --env-file .env celery -A config.celery_app worker -l info

celery-beat: ## Run Celery beat locally
	uv run --env-file .env celery -A config.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

shell: ## Open Django shell
	uv run --env-file .env manage.py shell

dbshell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d inclusive_world_portal
