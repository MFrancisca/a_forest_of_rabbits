from .base import *  # noqa: F401, F403

from decouple import config

DEBUG = False

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Database — read individual components from env via python-decouple
# Uses psycopg3 (psycopg[binary]) driver
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='esperanza'),
        'USER': config('POSTGRES_USER', default='postgres'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='db'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}

# Static files — whitenoise compressed manifest storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
