# syntax=docker/dockerfile:1

# Build stage: Python dependencies
FROM python:3.13-alpine AS builder

# Install build dependencies for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev \
    # WeasyPrint dependencies
    cairo-dev \
    pango-dev \
    gdk-pixbuf-dev \
    # Git for installing from repositories
    git

WORKDIR /app

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies (including dev dependencies for testing/linting)
RUN uv sync --frozen --no-install-project

# Development stage: Python dependencies with dev packages
FROM python:3.13-alpine AS development

# Install build and runtime dependencies for development
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    postgresql-libs \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    jpeg-dev \
    jpeg \
    zlib-dev \
    zlib \
    freetype-dev \
    freetype \
    lcms2-dev \
    lcms2 \
    openjpeg-dev \
    openjpeg \
    tiff-dev \
    tiff \
    tk-dev \
    tk \
    tcl-dev \
    tcl \
    harfbuzz-dev \
    harfbuzz \
    fribidi-dev \
    fribidi \
    libimagequant-dev \
    libimagequant \
    libxcb-dev \
    libxcb \
    libpng-dev \
    libpng \
    cairo-dev \
    cairo \
    pango-dev \
    pango \
    gdk-pixbuf-dev \
    gdk-pixbuf \
    fontconfig-dev \
    fontconfig \
    ttf-dejavu \
    ttf-liberation \
    font-noto \
    poppler-utils \
    bash \
    curl \
    git

# Configure fontconfig cache
RUN fc-cache -fv

# Create app user
RUN addgroup -g 1000 django && \
    adduser -D -u 1000 -G django django

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies including dev
RUN uv sync --frozen --no-install-project

# Switch to non-root user
USER django

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Development uses runserver by default
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM python:3.13-alpine AS production

# Install runtime dependencies
RUN apk add --no-cache \
    postgresql-libs \
    jpeg \
    zlib \
    freetype \
    lcms2 \
    openjpeg \
    tiff \
    tk \
    tcl \
    harfbuzz \
    fribidi \
    libimagequant \
    libxcb \
    libpng \
    # WeasyPrint runtime dependencies
    cairo \
    pango \
    gdk-pixbuf \
    fontconfig \
    # Fonts for PDF generation
    ttf-dejavu \
    ttf-liberation \
    font-noto \
    # PDF thumbnail generation
    poppler-utils \
    # Additional utilities
    bash \
    curl

# Configure fontconfig cache
RUN fc-cache -fv

# Create app user
RUN addgroup -g 1000 django && \
    adduser -D -u 1000 -G django django

WORKDIR /app

# Copy Python virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=django:django . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/inclusive_world_portal/media && \
    chown -R django:django /app/staticfiles /app/inclusive_world_portal/media

# Switch to non-root user
USER django

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set build-time environment variables with defaults for collectstatic
# These can be overridden at build time with --build-arg
ARG AWS_ACCESS_KEY_ID=minioadmin
ARG AWS_SECRET_ACCESS_KEY=minioadmin
ARG AWS_STORAGE_BUCKET_NAME=inclusive-world-media
ARG AWS_S3_ENDPOINT_URL=http://minio:9000
ARG AWS_S3_REGION_NAME=us-east-1
ARG DJANGO_SECRET_KEY=build-time-secret-key-only-for-collectstatic

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME} \
    AWS_S3_ENDPOINT_URL=${AWS_S3_ENDPOINT_URL} \
    AWS_S3_REGION_NAME=${AWS_S3_REGION_NAME} \
    DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Make entrypoint executable
USER root
COPY --chown=django:django compose/production/django/entrypoint /entrypoint
RUN chmod +x /entrypoint

USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--worker-tmp-dir", "/dev/shm", "--max-requests", "1000", "--max-requests-jitter", "50", "--access-logfile", "-", "--error-logfile", "-"]
