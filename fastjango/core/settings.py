"""
FastJango Settings - Django-like settings management.

This module provides Django-like settings management for FastJango,
including ALLOWED_HOSTS, CORS, and other configuration options.
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class FastJangoSettings:
    """FastJango settings class similar to Django settings."""
    
    # Debug settings
    DEBUG: bool = field(default=False)
    
    # Host settings
    ALLOWED_HOSTS: List[str] = field(default_factory=lambda: ['*'])
    USE_X_FORWARDED_HOST: bool = field(default=False)
    USE_X_FORWARDED_PORT: bool = field(default=False)
    
    # CORS settings
    CORS_ALLOWED_ORIGINS: List[str] = field(default_factory=list)
    CORS_ALLOWED_ORIGIN_REGEXES: List[str] = field(default_factory=list)
    CORS_ALLOWED_METHODS: List[str] = field(default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    CORS_ALLOWED_HEADERS: List[str] = field(default_factory=list)
    CORS_EXPOSED_HEADERS: List[str] = field(default_factory=list)
    CORS_ALLOW_CREDENTIALS: bool = field(default=False)
    CORS_MAX_AGE: Optional[int] = field(default=None)
    CORS_ALLOW_ALL_ORIGINS: bool = field(default=False)
    CORS_ALLOW_ALL_METHODS: bool = field(default=False)
    CORS_ALLOW_ALL_HEADERS: bool = field(default=False)
    
    # Security settings
    SECRET_KEY: str = field(default="your-secret-key-here")
    SECURE_SSL_REDIRECT: bool = field(default=False)
    SECURE_SSL_HOST: Optional[str] = field(default=None)
    SECURE_CONTENT_TYPE_NOSNIFF: bool = field(default=True)
    SECURE_BROWSER_XSS_FILTER: bool = field(default=True)
    SECURE_FRAME_DENY: bool = field(default=True)
    SECURE_CONTENT_SECURITY_POLICY: Optional[str] = field(default=None)
    SECURE_REFERRER_POLICY: Optional[str] = field(default=None)
    SECURE_HSTS_SECONDS: int = field(default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = field(default=False)
    SECURE_HSTS_PRELOAD: bool = field(default=False)
    
    # Database settings
    DATABASES: Dict[str, Any] = field(default_factory=lambda: {
        'default': {
            'ENGINE': 'fastjango.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    })
    
    # Installed apps
    INSTALLED_APPS: List[str] = field(default_factory=list)
    
    # Middleware
    MIDDLEWARE: List[str] = field(default_factory=list)
    
    # Static files
    STATIC_URL: str = field(default='/static/')
    STATIC_ROOT: Optional[str] = field(default=None)
    STATICFILES_DIRS: List[str] = field(default_factory=list)
    
    # Media files
    MEDIA_URL: str = field(default='/media/')
    MEDIA_ROOT: Optional[str] = field(default=None)
    
    # Templates
    TEMPLATES: List[Dict[str, Any]] = field(default_factory=list)
    
    # Logging
    LOGGING: Dict[str, Any] = field(default_factory=dict)
    
    # Session settings
    SESSION_COOKIE_NAME: str = field(default='sessionid')
    SESSION_COOKIE_AGE: int = field(default=1209600)  # 2 weeks
    SESSION_COOKIE_SECURE: bool = field(default=False)
    SESSION_COOKIE_HTTPONLY: bool = field(default=True)
    SESSION_COOKIE_SAMESITE: str = field(default='Lax')
    SESSION_EXPIRE_AT_BROWSER_CLOSE: bool = field(default=False)
    SESSION_SAVE_EVERY_REQUEST: bool = field(default=False)
    
    # Pagination settings
    PAGINATION_PAGE_SIZE: int = field(default=20)
    PAGINATION_MAX_PAGE_SIZE: int = field(default=100)
    
    # API settings
    API_PAGINATION_CLASS: str = field(default='fastjango.pagination.PageNumberPagination')
    API_DEFAULT_RENDERER_CLASSES: List[str] = field(default_factory=list)
    API_DEFAULT_PARSER_CLASSES: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Set default CORS settings if not provided
        if not self.CORS_ALLOWED_HEADERS:
            self.CORS_ALLOWED_HEADERS = [
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
        
        # Set default middleware if not provided
        if not self.MIDDLEWARE:
            self.MIDDLEWARE = [
                'fastjango.middleware.session.SessionMiddleware',
                'fastjango.middleware.authentication.AuthenticationMiddleware',
                'fastjango.middleware.security.SecurityMiddleware',
                'fastjango.middleware.cors.CORSMiddleware',
                'fastjango.middleware.common.CommonMiddleware',
                'fastjango.middleware.messages.MessageMiddleware',
            ]
        
        # Set default installed apps if not provided
        if not self.INSTALLED_APPS:
            self.INSTALLED_APPS = [
                'fastjango.core',
                'fastjango.db',
                'fastjango.api',
                'fastjango.forms',
                'fastjango.admin',
                'fastjango.static',
                'fastjango.media',
            ]


def load_settings_from_module(module_name: str) -> FastJangoSettings:
    """Load settings from a Python module."""
    import importlib
    
    try:
        module = importlib.import_module(module_name)
        settings = FastJangoSettings()
        
        # Load settings from module
        for attr_name in dir(module):
            if attr_name.isupper() and not attr_name.startswith('_'):
                attr_value = getattr(module, attr_name)
                if hasattr(settings, attr_name):
                    setattr(settings, attr_name, attr_value)
        
        return settings
    except ImportError:
        # Return default settings if module not found
        return FastJangoSettings()


def load_settings_from_dict(settings_dict: Dict[str, Any]) -> FastJangoSettings:
    """Load settings from a dictionary."""
    settings = FastJangoSettings()
    
    for key, value in settings_dict.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    return settings


def get_settings() -> FastJangoSettings:
    """Get settings from environment or defaults."""
    settings_module = os.environ.get('FASTJANGO_SETTINGS_MODULE')
    
    if settings_module:
        return load_settings_from_module(settings_module)
    else:
        return FastJangoSettings()


def validate_allowed_hosts(host: str, settings: FastJangoSettings) -> bool:
    """Validate if host is allowed."""
    if '*' in settings.ALLOWED_HOSTS:
        return True
    
    return host in settings.ALLOWED_HOSTS


def get_cors_settings(settings: FastJangoSettings) -> Dict[str, Any]:
    """Get CORS settings dictionary."""
    return {
        'allowed_origins': settings.CORS_ALLOWED_ORIGINS,
        'allowed_origin_regexes': settings.CORS_ALLOWED_ORIGIN_REGEXES,
        'allowed_methods': settings.CORS_ALLOWED_METHODS,
        'allowed_headers': settings.CORS_ALLOWED_HEADERS,
        'exposed_headers': settings.CORS_EXPOSED_HEADERS,
        'allow_credentials': settings.CORS_ALLOW_CREDENTIALS,
        'max_age': settings.CORS_MAX_AGE,
        'allow_all_origins': settings.CORS_ALLOW_ALL_ORIGINS,
        'allow_all_methods': settings.CORS_ALLOW_ALL_METHODS,
        'allow_all_headers': settings.CORS_ALLOW_ALL_HEADERS,
    }


def get_security_settings(settings: FastJangoSettings) -> Dict[str, Any]:
    """Get security settings dictionary."""
    return {
        'security_headers': {},
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'secure_ssl_redirect': settings.SECURE_SSL_REDIRECT,
        'secure_ssl_host': settings.SECURE_SSL_HOST,
        'secure_content_type_nosniff': settings.SECURE_CONTENT_TYPE_NOSNIFF,
        'secure_browser_xss_filter': settings.SECURE_BROWSER_XSS_FILTER,
        'secure_frame_deny': settings.SECURE_FRAME_DENY,
        'secure_content_security_policy': settings.SECURE_CONTENT_SECURITY_POLICY,
        'secure_referrer_policy': settings.SECURE_REFERRER_POLICY,
        'secure_hsts_seconds': settings.SECURE_HSTS_SECONDS,
        'secure_hsts_include_subdomains': settings.SECURE_HSTS_INCLUDE_SUBDOMAINS,
        'secure_hsts_preload': settings.SECURE_HSTS_PRELOAD,
    }


def get_session_settings(settings: FastJangoSettings) -> Dict[str, Any]:
    """Get session settings dictionary."""
    return {
        'session_cookie_name': settings.SESSION_COOKIE_NAME,
        'session_cookie_age': settings.SESSION_COOKIE_AGE,
        'session_cookie_secure': settings.SESSION_COOKIE_SECURE,
        'session_cookie_httponly': settings.SESSION_COOKIE_HTTPONLY,
        'session_cookie_samesite': settings.SESSION_COOKIE_SAMESITE,
        'session_expire_at_browser_close': settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
        'session_save_every_request': settings.SESSION_SAVE_EVERY_REQUEST,
    }


def get_pagination_settings(settings: FastJangoSettings) -> Dict[str, Any]:
    """Get pagination settings dictionary."""
    return {
        'page_size': settings.PAGINATION_PAGE_SIZE,
        'max_page_size': settings.PAGINATION_MAX_PAGE_SIZE,
        'pagination_class': settings.API_PAGINATION_CLASS,
    }


# Global settings instance
_settings = None


def get_settings_instance() -> FastJangoSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def configure_settings(settings_dict: Dict[str, Any]) -> None:
    """Configure settings from dictionary."""
    global _settings
    _settings = load_settings_from_dict(settings_dict)


def configure_from_module(module_name: str) -> None:
    """Configure settings from module."""
    global _settings
    _settings = load_settings_from_module(module_name)
