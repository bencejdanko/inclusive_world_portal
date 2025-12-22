"""Pytest configuration for user tests."""

import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def _allow_async_unsafe():
    """Allow Django to run database queries in async context during tests."""
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    yield
    del os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"]
