"""
FastJango Static Files - Django-like static file serving using FastAPI.
"""

import os
import hashlib
import mimetypes
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.staticfiles import StaticFiles as FastAPIStaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware


class StaticFiles:
    """
    Django-like static files handler using FastAPI's StaticFiles.
    
    This provides a familiar API for Django developers while leveraging
    FastAPI's performance and features.
    """
    
    def __init__(self, directory: str = "static", url_prefix: str = "/static/",
                 check_dir: bool = True, html: bool = False):
        """
        Initialize static files handler.
        
        Args:
            directory: Directory containing static files
            url_prefix: URL prefix for static files
            check_dir: Whether to check if directory exists
            html: Whether to serve HTML files
        """
        self.directory = Path(directory)
        self.url_prefix = url_prefix.rstrip('/')
        self.check_dir = check_dir
        self.html = html
        
        if check_dir and not self.directory.exists():
            raise ValueError(f"Static files directory does not exist: {directory}")
        
        # Initialize FastAPI StaticFiles
        self._static_files = FastAPIStaticFiles(
            directory=str(self.directory),
            html=html
        )
    
    def mount(self, app: FastAPI, name: str = "static"):
        """
        Mount static files to FastAPI app.
        
        Args:
            app: The FastAPI app
            name: The mount name
        """
        app.mount(self.url_prefix, self._static_files, name=name)
    
    def get_url(self, filename: str) -> str:
        """
        Get the URL for a static file.
        
        Args:
            filename: The filename
            
        Returns:
            The static file URL
        """
        return f"{self.url_prefix}/{filename.lstrip('/')}"
    
    def exists(self, filename: str) -> bool:
        """
        Check if a static file exists.
        
        Args:
            filename: The filename
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.directory / filename.lstrip('/')
        return file_path.exists() and file_path.is_file()
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """
        Get information about a static file.
        
        Args:
            filename: The filename
            
        Returns:
            Dictionary with file information
        """
        file_path = self.directory / filename.lstrip('/')
        
        if not file_path.exists() or not file_path.is_file():
            return {}
        
        stat = file_path.stat()
        content_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            'name': filename,
            'path': str(file_path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'content_type': content_type or 'application/octet-stream',
            'url': self.get_url(filename)
        }
    
    def list_files(self, subdirectory: str = "") -> List[Dict[str, Any]]:
        """
        List static files in a subdirectory.
        
        Args:
            subdirectory: The subdirectory to list
            
        Returns:
            List of file information dictionaries
        """
        dir_path = self.directory / subdirectory.lstrip('/')
        
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        
        files = []
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.directory)
                files.append(self.get_file_info(str(rel_path)))
        
        return files


class StaticFilesHandler:
    """
    Handler for serving static files with Django-like API.
    """
    
    def __init__(self, static_dirs: List[str] = None, static_url: str = "/static/"):
        """
        Initialize static files handler.
        
        Args:
            static_dirs: List of static directories
            static_url: URL prefix for static files
        """
        self.static_dirs = static_dirs or ["static"]
        self.static_url = static_url.rstrip('/')
        self._handlers = {}
        
        # Create handlers for each static directory
        for static_dir in self.static_dirs:
            handler = StaticFiles(directory=static_dir, url_prefix=self.static_url)
            self._handlers[static_dir] = handler
    
    def mount_all(self, app: FastAPI):
        """
        Mount all static file handlers to FastAPI app.
        
        Args:
            app: The FastAPI app
        """
        for i, (static_dir, handler) in enumerate(self._handlers.items()):
            mount_name = f"static_{i}" if i > 0 else "static"
            handler.mount(app, name=mount_name)
    
    def find_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Find a static file in any of the static directories.
        
        Args:
            filename: The filename to find
            
        Returns:
            File information or None if not found
        """
        for static_dir, handler in self._handlers.items():
            if handler.exists(filename):
                return handler.get_file_info(filename)
        return None
    
    def get_url(self, filename: str) -> str:
        """
        Get the URL for a static file.
        
        Args:
            filename: The filename
            
        Returns:
            The static file URL
        """
        return f"{self.static_url}/{filename.lstrip('/')}"


def collectstatic(source_dirs: List[str], destination: str, 
                 ignore_patterns: List[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Collect static files from multiple directories to a single location.
    
    Args:
        source_dirs: List of source directories
        destination: Destination directory
        ignore_patterns: Patterns to ignore
        dry_run: Whether to perform a dry run
        
    Returns:
        Dictionary with collection results
    """
    import shutil
    from pathlib import Path
    
    destination_path = Path(destination)
    ignore_patterns = ignore_patterns or []
    
    if not dry_run:
        destination_path.mkdir(parents=True, exist_ok=True)
    
    collected_files = []
    skipped_files = []
    
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            continue
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_path)
                
                # Check ignore patterns
                should_ignore = False
                for pattern in ignore_patterns:
                    if pattern in str(rel_path):
                        should_ignore = True
                        break
                
                if should_ignore:
                    skipped_files.append(str(rel_path))
                    continue
                
                dest_file = destination_path / rel_path
                
                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file)
                
                collected_files.append(str(rel_path))
    
    return {
        'collected_files': collected_files,
        'skipped_files': skipped_files,
        'total_collected': len(collected_files),
        'total_skipped': len(skipped_files)
    }


def find_static_files(directory: str, pattern: str = "*") -> List[str]:
    """
    Find static files matching a pattern.
    
    Args:
        directory: The directory to search
        pattern: The file pattern to match
        
    Returns:
        List of matching file paths
    """
    from pathlib import Path
    
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    
    files = []
    for file_path in dir_path.rglob(pattern):
        if file_path.is_file():
            files.append(str(file_path.relative_to(dir_path)))
    
    return files


def get_static_url(filename: str, static_url: str = "/static/") -> str:
    """
    Get the URL for a static file.
    
    Args:
        filename: The filename
        static_url: The static URL prefix
        
    Returns:
        The static file URL
    """
    return f"{static_url.rstrip('/')}/{filename.lstrip('/')}"


def serve_static_file(file_path: str, content_type: str = None) -> Response:
    """
    Serve a static file with proper headers.
    
    Args:
        file_path: The file path
        content_type: The content type
        
    Returns:
        FileResponse with proper headers
    """
    from pathlib import Path
    
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    if content_type is None:
        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or 'application/octet-stream'
    
    # Add cache headers
    stat = path.stat()
    etag = hashlib.md5(f"{path}:{stat.st_mtime}:{stat.st_size}".encode()).hexdigest()
    
    response = FileResponse(
        path=str(path),
        media_type=content_type,
        headers={
            'ETag': f'"{etag}"',
            'Cache-Control': 'public, max-age=31536000',  # 1 year
            'Last-Modified': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stat.st_mtime))
        }
    )
    
    return response


# Example usage:
def setup_static_files(app: FastAPI, settings: Dict[str, Any]):
    """
    Set up static files for a FastAPI app using Django-like settings.
    
    Args:
        app: The FastAPI app
        settings: Settings dictionary with static file configuration
    """
    static_url = settings.get('STATIC_URL', '/static/')
    static_root = settings.get('STATIC_ROOT')
    staticfiles_dirs = settings.get('STATICFILES_DIRS', [])
    
    if staticfiles_dirs:
        # Development: serve from multiple directories
        handler = StaticFilesHandler(
            static_dirs=staticfiles_dirs,
            static_url=static_url
        )
        handler.mount_all(app)
    elif static_root:
        # Production: serve from collected static files
        static_files = StaticFiles(
            directory=static_root,
            url_prefix=static_url
        )
        static_files.mount(app)
    else:
        # Default: serve from 'static' directory
        static_files = StaticFiles(
            directory="static",
            url_prefix=static_url
        )
        static_files.mount(app)
    
    # Add static file utilities to app state
    app.state.static_url = static_url
    app.state.static_root = static_root
    app.state.staticfiles_dirs = staticfiles_dirs
