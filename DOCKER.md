# Docker Setup Guide

This document provides comprehensive information about the Docker setup for the Inclusive World Portal.

## Overview

The Docker setup includes:

- **Multi-stage Dockerfile** for optimized production builds
- **Docker Compose** for orchestrating multiple services
- **Development and Production** configurations
- **Persistent data volumes** for PostgreSQL, Redis, and media files
- **Health checks** for service reliability
- **Idempotent migrations** and initialization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐ │
│  │ Django   │  │ Celery   │  │ Celery     │  │ Postgres  │ │
│  │ Web App  │  │ Worker   │  │ Beat       │  │ Database  │ │
│  │ :8000    │  │          │  │ Scheduler  │  │ :5432     │ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └─────┬─────┘ │
│       │             │              │               │        │
│       └─────────────┴──────────────┴───────────────┘        │
│                          │                                   │
│                    ┌─────┴──────┐                           │
│                    │   Redis    │                           │
│                    │   Cache    │                           │
│                    │   :6379    │                           │
│                    └────────────┘                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Files

### Core Files

- **Dockerfile**: Multi-stage build for Django application
- **docker-compose.yml**: Base production configuration
- **docker-compose.override.yml**: Development overrides (auto-loaded)
- **docker-compose.prod.yml**: Explicit production configuration with resource limits
- **.dockerignore**: Excludes unnecessary files from builds
- **compose/production/django/entrypoint**: Startup script with migrations

### Environment Files

- **.env.docker**: Active environment configuration
- **.env.docker.example**: Template for environment variables

## Quick Start

### Development Mode

```bash
# Start all services (auto-loads override for development)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Mode

```bash
# Option 1: Use explicit production file
docker-compose -f docker-compose.prod.yml up -d

# Option 2: Remove override and use base file
mv docker-compose.override.yml docker-compose.override.yml.bak
docker-compose up -d
```

## Services

### Django Web Application

**Development**:
- Uses Django's `runserver` for hot-reloading
- Mounts source code as volume
- Uses `local.py` settings
- Debug toolbar enabled
- Console email backend

**Production**:
- Uses Gunicorn with 4 workers
- Uses `production.py` settings
- All security headers enabled
- SMTP email backend
- Static files compressed with WhiteNoise

**Environment Variables**:
```env
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<random-50-char-string>
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_DEBUG=False
```

### PostgreSQL Database

**Configuration**:
- PostgreSQL 17 Alpine Linux
- Persistent volume: `postgres_data`
- Health checks every 10 seconds
- Auto-restarts on failure

**Environment Variables**:
```env
POSTGRES_DB=inclusive_world_portal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme_in_production
```

**Access Database**:
```bash
# Via Docker
docker-compose exec postgres psql -U postgres -d inclusive_world_portal

# Create backup
docker-compose exec postgres pg_dump -U postgres inclusive_world_portal > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres -d inclusive_world_portal < backup.sql
```

### Redis Cache

**Configuration**:
- Redis 7 Alpine Linux
- Persistent volume: `redis_data`
- AOF persistence enabled
- Memory limit: 256MB (production)
- LRU eviction policy

**Access Redis**:
```bash
docker-compose exec redis redis-cli
```

### Celery Worker

**Configuration**:
- Processes background tasks
- Max 1000 tasks per child (prevents memory leaks)
- Shares media volume with Django

**Monitor Tasks**:
```bash
# View worker logs
docker-compose logs -f celeryworker

# Inspect active tasks
docker-compose exec celeryworker celery -A config.celery_app inspect active
```

### Celery Beat Scheduler

**Configuration**:
- Schedules periodic tasks
- Uses Django database scheduler
- Persistent schedule volume

## Data Persistence

All data is stored in Docker volumes:

```bash
# List volumes
docker volume ls | grep inclusive_world_portal

# Inspect volume
docker volume inspect inclusive_world_portal_postgres_data

# Backup volume
docker run --rm -v inclusive_world_portal_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v inclusive_world_portal_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### Volume Details

| Volume | Purpose | Size (typical) |
|--------|---------|----------------|
| postgres_data | Database files | 100MB - 10GB |
| redis_data | Redis persistence | 10MB - 256MB |
| media_volume | User uploads | Varies |
| static_volume | CSS/JS/Images | 50MB - 200MB |
| celerybeat_schedule | Scheduler state | < 1MB |

## Environment Configuration

### Required Variables

```env
# Database
POSTGRES_DB=inclusive_world_portal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secure-password>

# Django
DJANGO_SECRET_KEY=<random-50-character-string>
DJANGO_ALLOWED_HOSTS=localhost,your-domain.com
```

### Optional Variables

```env
# Security
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000

# Email
EMAIL_URL=smtp+tls://user%40domain.com:password@smtp.gmail.com:587
DJANGO_DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# Payments
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Common Tasks

### Migrations

```bash
# Run migrations (idempotent)
docker-compose exec django python manage.py migrate

# Create migrations
docker-compose exec django python manage.py makemigrations

# Show migration status
docker-compose exec django python manage.py showmigrations
```

### User Management

```bash
# Create superuser
docker-compose exec django python manage.py createsuperuser

# Change user password
docker-compose exec django python manage.py changepassword <username>
```

### Static Files

```bash
# Collect static files
docker-compose exec django python manage.py collectstatic --noinput

# Clear static files
docker-compose exec django python manage.py collectstatic --noinput --clear
```

### Testing

```bash
# Run all tests
docker-compose exec django python manage.py test

# Run specific test
docker-compose exec django python manage.py test inclusive_world_portal.users.tests.test_models

# Run with pytest
docker-compose exec django pytest

# Run with coverage
docker-compose exec django coverage run -m pytest
docker-compose exec django coverage report
docker-compose exec django coverage html
```

### Shell Access

```bash
# Django shell
docker-compose exec django python manage.py shell

# Django shell with iPython
docker-compose exec django python manage.py shell_plus

# Bash shell
docker-compose exec django bash

# Root shell (if needed)
docker-compose exec -u root django bash
```

## Makefile Commands

For convenience, use the included Makefile:

```bash
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make logs           # View all logs
make logs-django    # View Django logs only
make shell          # Open Django shell
make migrate        # Run migrations
make test           # Run tests
make clean          # Stop and remove containers
make rebuild        # Rebuild and restart all services
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs <service-name>

# Check resource usage
docker stats

# Restart specific service
docker-compose restart <service-name>
```

### Database Issues

```bash
# Check database connection
docker-compose exec django python manage.py dbshell

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d

# Check migrations
docker-compose exec django python manage.py showmigrations
```

### Permission Issues

```bash
# Fix permissions (if running as root)
docker-compose exec -u root django chown -R django:django /app

# Check current user
docker-compose exec django whoami
```

### Port Conflicts

```bash
# Change port in docker-compose.yml
services:
  django:
    ports:
      - "8001:8000"  # Use different host port
```

### Out of Disk Space

```bash
# Remove unused containers, images, volumes
docker system prune -af --volumes

# Remove specific volume (⚠️ deletes data)
docker volume rm inclusive_world_portal_postgres_data
```

### Performance Issues

```bash
# Check resource limits
docker-compose -f docker-compose.prod.yml config

# Increase resources (docker-compose.prod.yml)
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

## Security Best Practices

### Production Checklist

- [ ] Generate new `DJANGO_SECRET_KEY`
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Configure `DJANGO_ALLOWED_HOSTS` with actual domains
- [ ] Enable SSL/TLS (`DJANGO_SECURE_SSL_REDIRECT=True`)
- [ ] Set up proper SMTP email backend
- [ ] Configure Sentry for error tracking
- [ ] Use environment-specific Stripe keys
- [ ] Enable HSTS headers
- [ ] Set up regular database backups
- [ ] Configure log rotation
- [ ] Use secrets management (Docker secrets or external vault)
- [ ] Enable firewall rules
- [ ] Set up monitoring and alerts

### Environment Variables Security

**DO NOT**:
- Commit `.env.docker` to version control
- Use default passwords in production
- Expose ports publicly without authentication

**DO**:
- Use `.env.docker.example` as template
- Generate strong random passwords
- Use Docker secrets for sensitive data
- Rotate credentials regularly

## Deployment

### Initial Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd inclusive_world_portal

# 2. Create environment file
cp .env.docker.example .env.docker
# Edit .env.docker with production values

# 3. Build and start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Create superuser
docker-compose exec django python manage.py createsuperuser

# 5. Verify deployment
docker-compose ps
docker-compose logs -f
```

### Updates and Rollbacks

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Rollback (if needed)
git checkout <previous-commit>
docker-compose -f docker-compose.prod.yml up -d --build
```

### Scaling

```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celeryworker=4

# Scale Django instances (requires load balancer)
docker-compose -f docker-compose.prod.yml up -d --scale django=3
```

## Monitoring

### Health Checks

All services include health checks:

```bash
# View health status
docker-compose ps

# Inspect health check logs
docker inspect --format='{{json .State.Health}}' inclusive_world_portal_django_prod | jq
```

### Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f django

# View last N lines
docker-compose logs --tail=100 django

# View logs with timestamps
docker-compose logs -t -f
```

### Resource Usage

```bash
# Real-time stats
docker stats

# Container resource usage
docker-compose top
```

## Advanced Configuration

### Custom Gunicorn Settings

Edit the CMD in Dockerfile:

```dockerfile
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gevent", \
     "--timeout", "120"]
```

### Custom Celery Settings

Edit command in docker-compose.yml:

```yaml
command: celery -A config.celery_app worker -l info --autoscale=10,2 --max-tasks-per-child=1000
```

### Additional Services

Add to docker-compose.yml:

```yaml
services:
  # Flower (Celery monitoring)
  flower:
    image: mher/flower
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    networks:
      - app_network
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this guide
3. Check Docker documentation
4. Contact development team

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
