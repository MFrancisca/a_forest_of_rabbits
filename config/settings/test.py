"""
Test settings — uses SQLite in-memory database so tests run without PostgreSQL.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

SECRET_KEY = 'insecure-test-secret-key-for-testing-only'

ALLOWED_HOSTS = ['*']

# Use SQLite in-memory database for tests — no PostgreSQL required
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Suppress debug toolbar in tests
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']  # noqa: F405

# Wagtail requires at least one site — tests create it via migrations
