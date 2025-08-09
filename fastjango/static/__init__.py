"""
FastJango Static Files - Django-like static file serving using FastAPI.
"""

from .files import (
    StaticFiles, StaticFilesHandler, collectstatic,
    find_static_files, get_static_url, serve_static_file
)
from .storage import (
    StaticStorage, FileSystemStorage, S3Storage,
    StaticFileStorage, DefaultStorage
)
from .middleware import StaticFilesMiddleware
from .utils import (
    static_url, static_root, staticfiles_urlpatterns,
    get_static_path, is_static_file, get_static_file_info
)

__all__ = [
    # Core static files
    'StaticFiles', 'StaticFilesHandler', 'collectstatic',
    'find_static_files', 'get_static_url', 'serve_static_file',
    
    # Storage
    'StaticStorage', 'FileSystemStorage', 'S3Storage',
    'StaticFileStorage', 'DefaultStorage',
    
    # Middleware
    'StaticFilesMiddleware',
    
    # Utils
    'static_url', 'static_root', 'staticfiles_urlpatterns',
    'get_static_path', 'is_static_file', 'get_static_file_info',
]
