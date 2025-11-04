#!/bin/bash

# Docker Environment Setup Script
# This script helps you create a production-ready .env.docker file

set -e

echo "================================================"
echo "Inclusive World Portal - Docker Environment Setup"
echo "================================================"
echo ""

# Check if .env.docker exists
if [ -f .env.docker ]; then
    echo "⚠️  .env.docker already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Keeping existing .env.docker"
        exit 0
    fi
    echo "Creating backup: .env.docker.backup"
    cp .env.docker .env.docker.backup
fi

# Copy template
cp .env.docker.example .env.docker

echo "✅ Created .env.docker from template"
echo ""
echo "⚙️  Generating secure values..."
echo ""

# Generate Django secret key
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
echo "Generated DJANGO_SECRET_KEY"

# Generate PostgreSQL password
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
echo "Generated POSTGRES_PASSWORD"

# Update .env.docker with generated values
sed -i "s|DJANGO_SECRET_KEY=changeme_to_a_50_character_random_string|DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY|g" .env.docker
sed -i "s|POSTGRES_PASSWORD=changeme_in_production|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env.docker

echo ""
echo "✅ Updated .env.docker with secure random values"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo ""
echo "1. Edit .env.docker and update the following:"
echo "   - DJANGO_ALLOWED_HOSTS (add your domain)"
echo "   - EMAIL_URL (your SMTP settings)"
echo "   - STRIPE_PUBLIC_KEY (production key)"
echo "   - STRIPE_SECRET_KEY (production key)"
echo "   - STRIPE_WEBHOOK_SECRET (production webhook)"
echo "   - SENTRY_DSN (your Sentry project DSN)"
echo ""
echo "2. Review security settings:"
echo "   - DJANGO_SECURE_SSL_REDIRECT"
echo "   - DJANGO_SECURE_HSTS_SECONDS"
echo ""
echo "3. Start your services:"
echo "   docker-compose up -d"
echo ""
echo "================================================"
echo ""

# Prompt for domain
read -p "Enter your domain name (or press Enter to skip): " DOMAIN
if [ ! -z "$DOMAIN" ]; then
    sed -i "s|DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com|DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN|g" .env.docker
    echo "✅ Updated DJANGO_ALLOWED_HOSTS with: $DOMAIN"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Never commit .env.docker to version control"
echo "   - Keep your .env.docker.backup in a secure location"
echo "   - Rotate secrets regularly"
echo ""
