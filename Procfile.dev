web: gunicorn config.wsgi:application --bind 0.0.0.0:8002 --workers 2 --reload --reload-extra-file inclusive_world_portal/templates --access-logfile - --error-logfile -
worker: celery -A config.celery_app worker -l info
beat: celery -A config.celery_app beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler