"""
Test settings — uses SQLite in-memory database so tests run without PostgreSQL.
"""
import tempfile

from .base import *  # noqa: F401, F403

DEBUG = True

# Isolate uploaded test files (e.g. wagtail_factories.ImageFactory) from the
# real media/ directory — avoids polluting it and sidesteps permission issues
# when media/ is root-owned from prior Docker writes.
MEDIA_ROOT = tempfile.mkdtemp()

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

# Wagtail requires at least one site — tests create it via migrations.
# Tests run the real blog/migrations (no MIGRATION_MODULES override), so data
# migrations and any model/migration drift are exercised too.
