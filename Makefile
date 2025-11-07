.PHONY: help build up down logs restart shell migrate makemigrations superuser test clean prune

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-django: ## View Django logs only
	docker-compose logs -f django

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
	docker-compose exec django python manage.py makemigrations

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

rebuild: down build up ## Rebuild and restart all services

prod-up: ## Start services in production mode
	docker-compose -f docker-compose.yml up -d

prod-logs: ## View production logs
	docker-compose -f docker-compose.yml logs -f

prod-down: ## Stop production services
	docker-compose -f docker-compose.yml down

dev-up: up ## Alias for up (development mode)

dev-logs: logs ## Alias for logs (development mode)

dev-down: down ## Alias for down (development mode)
