.PHONY: help up down install-dev install-prod run migrate makemigrations superuser test reset celery-worker celery-beat shell dbshell docs collectstatic

help:
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up:
	docker compose up -d

down:
	docker compose down

install-dev: ## Install all dependencies, including developer packages
	uv sync 

install-prod: ## Install only necessary packages, no developer packages
	uv sync --no-dev

run: ## Run the Django server, celery workers, and beat worker
	RUN_CELERY_WORKERS=true uv run --env-file .env honcho -f Procfile start

migrate: ## Run database migrations
	uv run --env-file .env manage.py migrate

makemigrations: ## Create new migrations
	uv run --env-file .env manage.py makemigrations

docs: ## Build documentation with MkDocs
	uv run mkdocs build

collectstatic: docs ## Collect static files (required after static file changes)
	uv run --env-file .env manage.py collectstatic --noinput

superuser: ## Create Django superuser
	uv run --env-file .env manage.py createsuperuser

mypy: ## Run mypy tests
	uv run --env-file .env mypy .

pytest: ## Run pytest tests
	uv run --env-file .env pytest

reset-migrations: ## Remove all migration files
	find inclusive_world_portal -path "*/migrations/*.py" -not -name "__init__.py" -delete

reset: reset-migrations ## Destroy all data (volumes), restart services and remove migrations
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
