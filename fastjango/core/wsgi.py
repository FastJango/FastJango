"""
WSGI application configuration for FastJango.
"""

import os
import sys
import importlib

from fastjango.core.logging import Logger

logger = Logger("fastjango.core.wsgi")


def get_settings():
    """
    Import and return the settings module.
    
    Returns:
        The settings module
    """
    settings_module = os.environ.get("FASTJANGO_SETTINGS_MODULE")
    if not settings_module:
        raise ImportError(
            "No settings module found. Set the FASTJANGO_SETTINGS_MODULE "
            "environment variable before importing fastjango.core.wsgi"
        )
    
    try:
        return importlib.import_module(settings_module)
    except ImportError as e:
        logger.error(f"Failed to import settings module: {e}", exc_info=True)
        raise ImportError(f"Failed to import settings module: {e}")


def get_wsgi_application():
    """
    Create and return a WSGI application for FastJango.
    
    Returns:
        The WSGI application
    """
    try:
        # Import settings
        settings = get_settings()
        
        # Django-like compatibility layer
        from fastjango.core.handlers.wsgi import WSGIHandler
        return WSGIHandler()
    except Exception as e:
        logger.error(f"Failed to create WSGI application: {e}", exc_info=True)
        raise 