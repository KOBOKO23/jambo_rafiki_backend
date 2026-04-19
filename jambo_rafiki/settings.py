"""
Django settings for jambo_rafiki project.
"""

from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)
DJANGO_ENV = config('DJANGO_ENV', default='development').lower().strip()

_raw_allowed_hosts = config('ALLOWED_HOSTS', default='', cast=Csv())
ALLOWED_HOSTS = [host.strip() for host in _raw_allowed_hosts if (host or '').strip()]

if DJANGO_ENV == 'production':
    if DEBUG:
        raise ImproperlyConfigured('DEBUG must be False in production')
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured('ALLOWED_HOSTS must be set in production')

SECRET_KEY = config('SECRET_KEY', default='')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-only-key-change-me'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set in production')
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'core',
    'contacts',
    'donations',
    'volunteers',
    'newsletter',
    'sponsorships',
    'gallery',
    'testimonials',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.RequestIdMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jambo_rafiki.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'jambo_rafiki' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jambo_rafiki.wsgi.application'

# Database
_raw_database_url = config('DATABASE_URL', default='sqlite:///db.sqlite3')


def _validate_production_database_configuration(database_url: str) -> None:
    """Fail fast when production database configuration is missing or unsafe."""
    if DJANGO_ENV != 'production':
        return

    normalized_database_url = (database_url or '').strip()
    if not normalized_database_url:
        raise ImproperlyConfigured('DATABASE_URL must be set in production')
    if normalized_database_url.startswith('sqlite:///') or normalized_database_url.startswith('sqlite://'):
        raise ImproperlyConfigured('DATABASE_URL must point to a non-SQLite production database')


_validate_production_database_configuration(_raw_database_url)

DATABASES = {
    'default': dj_database_url.config(
        default=_raw_database_url,
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MAX_IMAGE_UPLOAD_SIZE = config('MAX_IMAGE_UPLOAD_SIZE', default=5 * 1024 * 1024, cast=int)
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=10 * 1024 * 1024, cast=int)
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5 * 1024 * 1024, cast=int)

# Optional S3 media storage for production image hosting.
USE_S3_MEDIA = config('USE_S3_MEDIA', default=False, cast=bool)
if USE_S3_MEDIA:
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured('AWS_STORAGE_BUCKET_NAME must be set when USE_S3_MEDIA=True')

    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_LOCATION = config('AWS_MEDIA_LOCATION', default='media')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': config('AWS_MEDIA_CACHE_CONTROL', default='max-age=86400'),
    }

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'bucket_name': AWS_STORAGE_BUCKET_NAME,
                'region_name': AWS_S3_REGION_NAME,
                'location': AWS_LOCATION,
                'custom_domain': AWS_S3_CUSTOM_DOMAIN or None,
                'file_overwrite': AWS_S3_FILE_OVERWRITE,
                'default_acl': AWS_DEFAULT_ACL,
                'querystring_auth': AWS_QUERYSTRING_AUTH,
                'object_parameters': AWS_S3_OBJECT_PARAMETERS,
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"
    else:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_LOCATION}/"
    MEDIA_ROOT = None
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/minute',
        'user': '240/minute',
        'public_forms': '120/minute',
        'donation_initiation': '60/minute',
        'payment_callbacks': '120/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS Configuration

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='https://www.jamborafiki.org')

# CORS and CSRF origins from environment
_configured_cors_origins = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
if _configured_cors_origins:
    CORS_ALLOWED_ORIGINS = [origin.strip().rstrip('/') for origin in _configured_cors_origins if origin]
else:
    CORS_ALLOWED_ORIGINS = [FRONTEND_URL.rstrip('/')]

_configured_csrf_trusted = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
if _configured_csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [origin.strip().rstrip('/') for origin in _configured_csrf_trusted if origin]
else:
    CSRF_TRUSTED_ORIGINS = [FRONTEND_URL.rstrip('/')]

if DEBUG:
    for dev_origin in [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]:
        normalized = dev_origin.rstrip('/')
        if normalized not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(normalized)
        if normalized not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(normalized)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend' if DEBUG else '')
if not EMAIL_BACKEND:
    raise ImproperlyConfigured('EMAIL_BACKEND must be set in production')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


def _validate_production_email_configuration() -> None:
    """Fail fast when production SMTP settings are incomplete."""
    if DEBUG:
        return

    smtp_backends = {
        'django.core.mail.backends.smtp.EmailBackend',
        'anymail.backends.smtp.EmailBackend',
    }
    if EMAIL_BACKEND not in smtp_backends:
        return

    missing = []
    if not EMAIL_HOST.strip():
        missing.append('EMAIL_HOST')
    if not EMAIL_PORT:
        missing.append('EMAIL_PORT')
    if not EMAIL_HOST_USER.strip():
        missing.append('EMAIL_HOST_USER')
    if not EMAIL_HOST_PASSWORD.strip():
        missing.append('EMAIL_HOST_PASSWORD')

    if missing:
        missing_values = ', '.join(missing)
        raise ImproperlyConfigured(
            f'SMTP email backend requires {missing_values} in production'
        )


_validate_production_email_configuration()

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='info@jamborafiki.org')
ADMIN_NOTIFICATION_EMAILS = ['info@jamborafiki.org']
ADMIN_EMAIL = config('ADMIN_EMAIL', default='info@jamborafiki.org')

# Public organization identity/contact/banking details for frontend consumption.
ORGANIZATION_DOMAIN = config('ORGANIZATION_DOMAIN', default='')
ORGANIZATION_WEBSITE_URL = config('ORGANIZATION_WEBSITE_URL', default='')
ORGANIZATION_PUBLIC_EMAIL = config('ORGANIZATION_PUBLIC_EMAIL', default='info@jamborafiki.org')
ORGANIZATION_CALL_REDIRECT_NUMBER = config('ORGANIZATION_CALL_REDIRECT_NUMBER', default='+254799616542')

# M-Pesa Configuration
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_INITIATOR_NAME = config('MPESA_INITIATOR_NAME', default='testapi')
MPESA_SECURITY_CREDENTIAL = config('MPESA_SECURITY_CREDENTIAL', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')
MPESA_CALLBACK_TOKEN = config('MPESA_CALLBACK_TOKEN', default='')
MPESA_CALLBACK_SIGNATURE_SECRET = config('MPESA_CALLBACK_SIGNATURE_SECRET', default='')
MPESA_CALLBACK_SIGNATURE_HEADER = config('MPESA_CALLBACK_SIGNATURE_HEADER', default='X-MPESA-SIGNATURE')
if not MPESA_CALLBACK_TOKEN and not DEBUG:
    raise ImproperlyConfigured('MPESA_CALLBACK_TOKEN must be set in production')

# Stripe Configuration
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# PayPal Configuration
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID', default='')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET', default='')
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox')

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SESSION_COOKIE_HTTPONLY = True
    SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY', default='same-origin')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

_trusted_origins = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
CSRF_TRUSTED_ORIGINS = [origin.strip().rstrip('/') for origin in _trusted_origins if origin]

frontend_origin = FRONTEND_URL.strip().rstrip('/')
if frontend_origin and frontend_origin not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(frontend_origin)

if DEBUG:
    # Make local SPA/dev-server origins work out-of-the-box for CSRF-protected writes.
    dev_trusted_origins = [
        FRONTEND_URL,
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
    for origin in dev_trusted_origins:
        normalized = (origin or '').strip().rstrip('/')
        if normalized and normalized not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(normalized)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'core.logging_filters.RequestIdFilter',
        },
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': ['request_id'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'security.events': {
            'handlers': ['console'],
            'level': config('SECURITY_LOG_LEVEL', default='WARNING'),
            'propagate': False,
        },
    },
}

SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.0, cast=float),
        send_default_pii=False,
        environment=DJANGO_ENV,
    )
