# syntax=docker/dockerfile:1
# Dockerfile - Fast application image (rebuilds in ~30 seconds)
# Build: ./scripts/build-and-push.sh
# Rebuild: On every commit

FROM bencejdanko/inclusive-world-portal-deps:latest

WORKDIR /app

# Copy application code (this is the only layer that changes frequently)
COPY --chown=django:django . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/inclusive_world_portal/media && \
    chown -R django:django /app/staticfiles /app/inclusive_world_portal/media

# Switch to non-root user
USER django

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set build-time environment variables with defaults for collectstatic
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
