from .base import *  # noqa: F401, F403

import os

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY', 'insecure-dev-secret-key-change-in-production')

ALLOWED_HOSTS = ['*']

# DATABASE_PUBLIC_URL is set by Railway when connecting via shell or `railway run`.
# Fall back to individual POSTGRES_* vars for local Docker Compose.
_db_url = os.environ.get('DATABASE_PUBLIC_URL')
if _db_url:
    DATABASES = {'default': dj_database_url.parse(_db_url)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'esperanza'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# django-debug-toolbar
INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']  # noqa: F405

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ['127.0.0.1']
