"""
With these settings, tests run faster.
"""

from pathlib import Path

import environ

# Read .env file BEFORE importing base settings so DATABASE_URL is available
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

from .base import *  # noqa: F403, E402
from .base import TEMPLATES

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="pylyQbw0NHHPvVfuR3Rp8HsFSkryEJI08G3rcs9CumPmtCSlBRzQcu37Qxhx9wiR",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"
# Your stuff...
# ------------------------------------------------------------------------------
