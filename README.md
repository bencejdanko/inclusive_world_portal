# inclusive_world_portal

A management portal for the Inclusive World team.


[![CI](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/ci.yml/badge.svg)](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/ci.yml)
[![Docker Build and Test](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/docker.yml/badge.svg)](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/docker.yml)
[![Security Scan](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/security-scan.yml/badge.svg)](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/security-scan.yml)
[![Build and Deploy](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/build-and-deploy.yml/badge.svg)](https://github.com/bencejdanko/inclusive_world_portal/actions/workflows/build-and-deploy.yml)

## Developers

```bash

```

## Quick Start (Docker)

```bash
make up

# Create superuser
make superuser

# View logs
make logs-django

# Stop (keeps data for next 'make start')
make down

# Restart without destroying data
make start
```

### Type checks

Running type checks with mypy:

    uv run mypy inclusive_world_portal

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    uv run coverage run -m pytest
    uv run coverage html
    uv run open htmlcov/index.html

#### Running tests with pytest

    uv run pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd inclusive_world_portal
uv run celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd inclusive_world_portal
uv run celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd inclusive_world_portal
uv run celery -A config.celery_app worker -B -l info
```

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Docker Setup (Recommended)

This project includes a production-ready Docker setup with support for both development and production environments.

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

### Quick Start (Development)

1. **Build and start all services**:
   ```bash
   docker-compose up -d
   ```

   This automatically:
   - Starts PostgreSQL with persistent data
   - Starts Redis for caching and Celery
   - Runs database migrations
   - Starts Django with hot-reloading
   - Starts Celery worker and beat scheduler

2. **View logs**:
   ```bash
   docker-compose logs -f django
   ```

3. **Create a superuser** (if not using the default):
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

4. **Access the application**:
   - Django: http://localhost:8000
   - Admin: http://localhost:8000/admin/

### Production Deployment

1. **Update environment variables**:
   ```bash
   cp .env.docker.example .env.docker
   # Edit .env.docker with production values
   ```

2. **Deploy with production settings**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

   Production mode:
   - Uses Gunicorn with optimized worker configuration
   - Disables debug mode
   - Enables security headers
   - Uses persistent volumes for data

### Docker Commands

**Start services**:
```bash
docker-compose up -d
```

**Stop services**:
```bash
docker-compose down
```

**Rebuild services** (after code changes):
```bash
docker-compose up -d --build
```

**View all logs**:
```bash
docker-compose logs -f
```

**Run management commands**:
```bash
docker-compose exec django python manage.py <command>
```

**Access Django shell**:
```bash
docker-compose exec django python manage.py shell
```

**Run migrations**:
```bash
docker-compose exec django python manage.py migrate
```

**Collect static files** (production):
```bash
docker-compose exec django python manage.py collectstatic --noinput
```

**Access database**:
```bash
docker-compose exec postgres psql -U postgres -d inclusive_world_portal
```

**Clean up volumes** (⚠️ deletes all data):
```bash
docker-compose down -v
```

### Services Architecture

The Docker setup includes:

- **postgres**: PostgreSQL 17 Alpine with persistent data volume
- **redis**: Redis 7 Alpine for caching and Celery broker
- **django**: Django application with Gunicorn (production) or runserver (dev)
- **celeryworker**: Celery worker for async tasks
- **celerybeat**: Celery beat for scheduled tasks

### Development vs Production

**Development** (default with `docker-compose up`):
- Uses `docker-compose.override.yml` automatically
- Hot-reloading enabled (code changes reflect immediately)
- Django debug toolbar enabled
- Console email backend
- SQLite or local PostgreSQL

**Production** (with `docker-compose -f docker-compose.yml up`):
- No override file loaded
- Gunicorn with 4 workers
- All security headers enabled
- SMTP email backend
- Optimized static file serving

### Persistent Data

All data is stored in Docker volumes:
- `postgres_data`: Database data
- `redis_data`: Redis persistence
- `media_volume`: User-uploaded files
- `static_volume`: Static files (CSS, JS, images)
- `celerybeat_schedule`: Celery beat schedule database

These volumes persist between container restarts and updates.

### Troubleshooting

**Port already in use**:
```bash
# Change the port mapping in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

**Reset database**:
```bash
docker-compose down -v
docker-compose up -d
```

**View detailed logs**:
```bash
docker-compose logs --tail=100 -f django
```

**Container won't start**:
```bash
# Check container status
docker-compose ps

# View specific container logs
docker-compose logs <service-name>

# Restart a specific service
docker-compose restart <service-name>
```

## Local Development (Without Docker)

### Run locally

```
set -a; [ -f .env ] && . .env; set +a

uv run python manage.py runserver 0.0.0.0:8000
```

## Deployment

The following details how to deploy this application.