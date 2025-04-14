"""
Settings for testproject project.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-fastjango-development-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    # FastJango apps
    "testproject.core",
    
    # Third-party apps
    
    # Your apps
]

# Middleware
MIDDLEWARE = [
    "fastjango.middleware.security.SecurityMiddleware",
    "fastjango.middleware.session.SessionMiddleware",
    "fastapi.middleware.cors.CORSMiddleware",
    "fastjango.middleware.common.CommonMiddleware",
    "fastjango.middleware.csrf.CsrfMiddleware",
    "fastjango.middleware.auth.AuthenticationMiddleware",
    "fastjango.middleware.messages.MessageMiddleware",
]

ROOT_URLCONF = "testproject.urls"

TEMPLATES = [
    {
        "BACKEND": "fastjango.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "fastjango.template.context_processors.debug",
                "fastjango.template.context_processors.request",
                "fastjango.template.context_processors.auth",
                "fastjango.template.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "testproject.wsgi.application"
ASGI_APPLICATION = "testproject.asgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "fastjango.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "fastjango.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "fastjango.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "fastjango.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "fastjango.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "fastjango.db.models.BigAutoField" 