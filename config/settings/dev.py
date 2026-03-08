from .base import *  # noqa: F401, F403

from decouple import config

DEBUG = True

SECRET_KEY = config('SECRET_KEY', default='insecure-dev-secret-key-change-in-production')

ALLOWED_HOSTS = ['*']

# Database — read individual components from env via python-decouple
# Uses psycopg3 (psycopg[binary]) driver
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='esperanza'),
        'USER': config('POSTGRES_USER', default='postgres'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='postgres'),
        'HOST': config('POSTGRES_HOST', default='db'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}

# django-debug-toolbar
INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']  # noqa: F405

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ['127.0.0.1']
