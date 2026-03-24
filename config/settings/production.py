from .base import *  # noqa: F401, F403
from decouple import config
import dj_database_url
import os

DEBUG = False

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Database — Railway PostgreSQL via DATABASE_URL (replaces individual POSTGRES_* vars)
DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'),conn_max_age=600, conn_health_checks=True)
}

# Media + static storage — Django 5.x STORAGES dict
# DEFAULT_FILE_STORAGE and STATICFILES_STORAGE were removed in Django 5.1
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": config('AWS_ACCESS_KEY_ID'),
            "secret_key": config('AWS_SECRET_ACCESS_KEY'),
            "bucket_name": config('AWS_STORAGE_BUCKET_NAME'),
            "endpoint_url": config('AWS_S3_ENDPOINT_URL'),
            "custom_domain": 'media.aforestofrabbits.art',
            "querystring_auth": False,
            "region_name": "auto",
            "signature_version": "s3v4",
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
MEDIA_URL = 'https://media.aforestofrabbits.art/'

# Security — Cloudflare terminates SSL; Django sees HTTP internally
# DO NOT set SECURE_SSL_REDIRECT — causes redirect loops behind Cloudflare proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://www.aforestofrabbits.art', 'https://*.up.railway.app']
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True

# Wagtail
WAGTAILADMIN_BASE_URL = 'https://www.aforestofrabbits.art'

# Logging — errors to console (Railway captures stdout/stderr)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
