# Docker Quick Reference

## 🚀 Quick Start

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f django

# Stop services
docker-compose down
```

## 📋 Common Commands

### Service Management
```bash
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View all logs
make logs-django     # View Django logs only
make ps              # Show running containers
```

### Development
```bash
make shell           # Open Django shell
make bash            # Open bash in container
make migrate         # Run migrations
make makemigrations  # Create migrations
make superuser       # Create superuser
make test            # Run tests
```

### Database
```bash
make dbshell         # Open PostgreSQL shell
make migrate         # Apply migrations
```

### Maintenance
```bash
make rebuild         # Rebuild and restart
make clean           # Stop and remove containers
make clean-volumes   # ⚠️ Remove containers AND data
```

## 🏭 Production

```bash
# Start production
docker-compose -f docker-compose.prod.yml up -d

# Or use makefile
make prod-up
make prod-logs
make prod-down
```

## 🔧 Management Commands

```bash
# Run any Django command
docker-compose exec django python manage.py <command>

# Examples:
docker-compose exec django python manage.py createsuperuser
docker-compose exec django python manage.py shell
docker-compose exec django python manage.py collectstatic
```

## 📊 Monitoring

```bash
# View logs
docker-compose logs -f [service]

# Check health
docker-compose ps

# Resource usage
docker stats

# Inspect service
docker-compose exec [service] ps aux
```

## 🗄️ Database Operations

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres inclusive_world_portal > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres inclusive_world_portal < backup.sql

# Connect to database
docker-compose exec postgres psql -U postgres -d inclusive_world_portal
```

## 🐛 Troubleshooting

```bash
# View detailed logs
docker-compose logs --tail=100 -f django

# Restart specific service
docker-compose restart django

# Rebuild specific service
docker-compose up -d --build django

# Check container status
docker-compose ps

# Access container as root
docker-compose exec -u root django bash
```

## 📁 File Structure

```
.
├── Dockerfile                      # Multi-stage build
├── docker-compose.yml              # Base configuration
├── docker-compose.override.yml     # Dev overrides
├── docker-compose.prod.yml         # Production config
├── .dockerignore                   # Build exclusions
├── .env.docker                     # Environment vars
├── .env.docker.example             # Template
├── compose/
│   └── production/
│       └── django/
│           └── entrypoint          # Startup script
├── Makefile                        # Convenience commands
└── DOCKER.md                       # Full documentation
```

## 🔐 Security Checklist

- [ ] Change POSTGRES_PASSWORD
- [ ] Set DJANGO_SECRET_KEY (50+ random chars)
- [ ] Configure DJANGO_ALLOWED_HOSTS
- [ ] Set DJANGO_DEBUG=False (production)
- [ ] Enable SSL (DJANGO_SECURE_SSL_REDIRECT=True)
- [ ] Configure SENTRY_DSN for monitoring
- [ ] Use production Stripe keys
- [ ] Review .env.docker values

## 🌐 Access URLs

- **Django**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **Flower** (if enabled): http://localhost:5555

## 📦 Volumes

Persistent data stored in:
- `postgres_data` - Database
- `redis_data` - Cache
- `media_volume` - User uploads
- `static_volume` - Static files
- `celerybeat_schedule` - Scheduler

## 💡 Tips

1. **Use Makefile**: Simplifies common tasks
2. **Check logs first**: Most issues visible in logs
3. **Health checks**: Wait for services to be healthy
4. **Idempotent**: Safe to run `up` multiple times
5. **Backups**: Regular database backups essential
6. **Resources**: Monitor with `docker stats`

## 📚 More Info

See `DOCKER.md` for comprehensive documentation.
