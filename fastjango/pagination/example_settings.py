"""
FastJango Settings Example - Django-like settings with ALLOWED_HOSTS and CORS.

This example demonstrates how to configure FastJango settings similar to Django,
including ALLOWED_HOSTS validation and comprehensive CORS configuration.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Django-like ALLOWED_HOSTS configuration
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'your-domain.com',
    'www.your-domain.com',
    # Add your production domains here
]

# CORS Configuration (Django-like)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://your-frontend-domain.com",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.your-domain\.com$",
    r"^https://\w+\.your-subdomain\.com$",
]

CORS_ALLOWED_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
]

CORS_EXPOSED_HEADERS = [
    'content-type',
    'content-length',
    'x-total-count',
    'x-page-count',
]

CORS_ALLOW_CREDENTIALS = True
CORS_MAX_AGE = 86400  # 24 hours

# For development only - disable in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_ALL_METHODS = False
CORS_ALLOW_ALL_HEADERS = False

# Security Settings
SECURE_SSL_REDIRECT = False  # Set to True in production
SECURE_SSL_HOST = None
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_SECURITY_POLICY = None
SECURE_REFERRER_POLICY = None
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Database Configuration (Django-like)
DATABASES = {
    'default': {
        'ENGINE': 'fastjango.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    # PostgreSQL example
    # 'default': {
    #     'ENGINE': 'fastjango.db.backends.postgresql',
    #     'NAME': 'your_db_name',
    #     'USER': 'your_db_user',
    #     'PASSWORD': 'your_db_password',
    #     'HOST': 'localhost',
    #     'PORT': '5432',
    # },
    # MySQL example
    # 'default': {
    #     'ENGINE': 'fastjango.db.backends.mysql',
    #     'NAME': 'your_db_name',
    #     'USER': 'your_db_user',
    #     'PASSWORD': 'your_db_password',
    #     'HOST': 'localhost',
    #     'PORT': '3306',
    # },
}

# Installed Apps (Django-like)
INSTALLED_APPS = [
    'fastjango.core',
    'fastjango.db',
    'fastjango.api',
    'fastjango.forms',
    'fastjango.admin',
    'fastjango.static',
    'fastjango.media',
    'fastjango.pagination',
    # Your apps here
    # 'myapp',
]

# Middleware Configuration (Django-like)
MIDDLEWARE = [
    'fastjango.middleware.security.SecurityMiddleware',
    'fastjango.middleware.session.SessionMiddleware',
    'fastjango.middleware.cors.CORSMiddleware',
    'fastjango.middleware.common.CommonMiddleware',
    'fastjango.middleware.authentication.AuthenticationMiddleware',
    'fastjango.middleware.messages.MessageMiddleware',
    'fastjango.middleware.gzip.GZipMiddleware',
]

# Static Files Configuration (Django-like)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media Files Configuration (Django-like)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Templates Configuration (Django-like)
TEMPLATES = [
    {
        'BACKEND': 'fastjango.templates.backends.jinja2.Jinja2Templates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'fastjango.templates.context_processors.debug',
                'fastjango.templates.context_processors.request',
            ],
        },
    },
]

# Session Configuration (Django-like)
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

# Pagination Configuration (Django-like)
PAGINATION_PAGE_SIZE = 20
PAGINATION_MAX_PAGE_SIZE = 100
API_PAGINATION_CLASS = 'fastjango.pagination.PageNumberPagination'

# API Configuration (Django-like)
API_DEFAULT_RENDERER_CLASSES = [
    'fastjango.api.renderers.JSONRenderer',
    'fastjango.api.renderers.BrowsableAPIRenderer',
]

API_DEFAULT_PARSER_CLASSES = [
    'fastjango.api.parsers.JSONParser',
    'fastjango.api.parsers.FormParser',
    'fastjango.api.parsers.MultiPartParser',
]

# Logging Configuration (Django-like)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'fastjango.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'fastjango': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Password validation (Django-like)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'fastjango.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'fastjango.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'fastjango.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'fastjango.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization (Django-like)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type (Django-like)
DEFAULT_AUTO_FIELD = 'fastjango.db.models.BigAutoField'

# Cache Configuration (Django-like)
CACHES = {
    'default': {
        'BACKEND': 'fastjango.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    # Redis example
    # 'default': {
    #     'BACKEND': 'fastjango.core.cache.backends.redis.RedisCache',
    #     'LOCATION': 'redis://127.0.0.1:6379/1',
    # },
}

# Email Configuration (Django-like)
EMAIL_BACKEND = 'fastjango.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

# File Upload Configuration (Django-like)
FILE_UPLOAD_HANDLERS = [
    'fastjango.core.files.uploadhandler.MemoryFileUploadHandler',
    'fastjango.core.files.uploadhandler.TemporaryFileUploadHandler',
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
FILE_UPLOAD_TEMP_DIR = None
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_SECURITY_POLICY = "default-src 'self'"
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Production CORS settings
    CORS_ALLOWED_ORIGINS = [
        "https://your-production-domain.com",
        "https://www.your-production-domain.com",
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_ALL_ORIGINS = False
