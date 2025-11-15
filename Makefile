.PHONY: help build up down logs restart shell migrate makemigrations superuser test clean prune

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up:
	docker-compose down --remove-orphans
	docker volume rm inclusive_world_portal_postgres_data || true
	docker volume rm inclusive_world_portal_redis_data || true
	docker volume rm inclusive_world_portal_minio_data || true
	docker volume rm inclusive_world_portal_static_volume || true
	docker volume rm inclusive_world_portal_media_volume || true
	docker volume rm inclusive_world_portal_celerybeat_schedule || true
	@echo "🗑️  Deleting old migrations..."
	rm -f inclusive_world_portal/portal/migrations/0*.py
	rm -f inclusive_world_portal/users/migrations/0*.py
	rm -f inclusive_world_portal/payments/migrations/0*.py
	@echo "All volumes and migrations removed"
	docker-compose build
	docker-compose up -d postgres redis minio
	@echo "⏳ Waiting for postgres to be ready..."
	@sleep 10
	docker-compose up -d django
	@echo "⏳ Waiting for Django to be ready..."
	@sleep 10
	@echo "🔄 Generating fresh migrations..."
	docker-compose exec -u root django python manage.py makemigrations || (echo "❌ Failed to generate migrations" && exit 1)
	@echo "🔄 Running migrations..."
	docker-compose exec django python manage.py migrate --noinput || (echo "❌ Failed to run migrations" && exit 1)
	docker-compose up -d
	@echo "✅ Fresh environment ready! Create superuser with: make superuser"

down: ## Stop all services (keeps volumes)
	docker-compose down

start: ## Start services without destroying data (use when 'up' already run once)
	docker-compose up -d

logs: ## View logs from all services
	docker-compose logs -f

logs-django: ## View Django logs only
	docker-compose logs -f django

logs-postgres: ## View Postgres logs only
	docker-compose logs -f postgres

restart: ## Restart all services
	docker-compose restart

restart-django: ## Restart Django service only
	docker-compose restart django

shell: ## Open Django shell
	docker-compose exec django python manage.py shell

bash: ## Open bash shell in Django container
	docker-compose exec django bash

dbshell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d inclusive_world_portal

migrate: ## Run database migrations
	docker-compose exec django python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose exec -u root django python manage.py makemigrations

makemigrations-root: ## Create new migrations as root (for packages that need write access)
	docker-compose exec -u root django python manage.py makemigrations

superuser: ## Create Django superuser
	docker-compose exec django python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec django python manage.py collectstatic --noinput

test: ## Run tests
	docker-compose exec django python manage.py test

pytest: ## Run pytest
	docker-compose exec django pytest

coverage: ## Run tests with coverage report
	docker-compose exec django coverage run -m pytest
	docker-compose exec django coverage html
	@echo "Coverage report available at htmlcov/index.html"

clean: ## Stop services and remove containers
	docker-compose down --remove-orphans

clean-volumes: ## Stop services and remove containers and volumes (⚠️ deletes data)
	docker-compose down -v --remove-orphans

prune: ## Remove all unused Docker resources
	docker system prune -af --volumes

ps: ## Show running containers
	docker-compose ps

debug-env: ## Show environment variables being used
	@echo "=== Environment from .env.docker ==="
	@grep -E "POSTGRES_|DATABASE_URL" .env.docker || echo "No postgres vars in .env.docker"
	@echo ""
	@echo "=== Postgres container environment ==="
	@docker-compose exec postgres env | grep POSTGRES || echo "Postgres not running"
	@echo ""
	@echo "=== Django container environment ==="
	@docker-compose exec django env | grep -E "POSTGRES_|DATABASE_URL" || echo "Django not running"

rebuild: up ## Alias for 'up' (nuclear rebuild)
