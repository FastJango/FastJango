"""
FastJango Static Files Middleware - Django-like static file middleware.
"""

import os
import mimetypes
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware


class StaticFilesMiddleware(BaseHTTPMiddleware):
    """
    Middleware for serving static files with Django-like behavior.
    
    This middleware intercepts requests to static files and serves them
    directly, similar to Django's static file middleware.
    """
    
    def __init__(self, app, static_url: str = "/static/", static_dirs: List[str] = None,
                 check_dir: bool = True, html: bool = False):
        """
        Initialize the static files middleware.
        
        Args:
            app: The FastAPI app
            static_url: URL prefix for static files
            static_dirs: List of static directories to search
            check_dir: Whether to check if directories exist
            html: Whether to serve HTML files
        """
        super().__init__(app)
        self.static_url = static_url.rstrip('/')
        self.static_dirs = static_dirs or ["static"]
        self.check_dir = check_dir
        self.html = html
        
        # Validate static directories
        if check_dir:
            for static_dir in self.static_dirs:
                if not Path(static_dir).exists():
                    raise ValueError(f"Static directory does not exist: {static_dir}")
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and serve static files if needed.
        
        Args:
            request: The request object
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Check if this is a static file request
        if request.url.path.startswith(self.static_url):
            return await self._serve_static_file(request)
        
        # Continue with normal request processing
        response = await call_next(request)
        return response
    
    async def _serve_static_file(self, request: Request) -> Response:
        """
        Serve a static file.
        
        Args:
            request: The request object
            
        Returns:
            FileResponse or 404 response
        """
        # Extract the file path from the URL
        url_path = request.url.path
        if not url_path.startswith(self.static_url):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Remove the static URL prefix to get the file path
        file_path = url_path[len(self.static_url):].lstrip('/')
        
        # Look for the file in static directories
        for static_dir in self.static_dirs:
            full_path = Path(static_dir) / file_path
            
            if full_path.exists() and full_path.is_file():
                return await self._create_file_response(full_path)
        
        # File not found
        raise HTTPException(status_code=404, detail="Static file not found")
    
    async def _create_file_response(self, file_path: Path) -> Response:
        """
        Create a FileResponse for a static file.
        
        Args:
            file_path: The file path
            
        Returns:
            FileResponse with proper headers
        """
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or 'application/octet-stream'
        
        # Get file stats
        stat = file_path.stat()
        
        # Create ETag for caching
        etag = self._generate_etag(file_path, stat)
        
        # Check if file has been modified
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and if_none_match == etag:
            return Response(status_code=304)  # Not Modified
        
        # Create response with cache headers
        response = FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers={
                'ETag': etag,
                'Cache-Control': 'public, max-age=31536000',  # 1 year
                'Last-Modified': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stat.st_mtime)),
                'Content-Length': str(stat.st_size)
            }
        )
        
        return response
    
    def _generate_etag(self, file_path: Path, stat) -> str:
        """
        Generate an ETag for a file.
        
        Args:
            file_path: The file path
            stat: File stats
            
        Returns:
            The ETag string
        """
        import hashlib
        
        # Create ETag based on file path, modification time, and size
        etag_data = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
        return f'"{hashlib.md5(etag_data.encode()).hexdigest()}"'
    
    def find_static_file(self, filename: str) -> Optional[Path]:
        """
        Find a static file in the static directories.
        
        Args:
            filename: The filename to find
            
        Returns:
            Path to the file or None if not found
        """
        for static_dir in self.static_dirs:
            file_path = Path(static_dir) / filename.lstrip('/')
            if file_path.exists() and file_path.is_file():
                return file_path
        return None
    
    def get_static_url(self, filename: str) -> str:
        """
        Get the URL for a static file.
        
        Args:
            filename: The filename
            
        Returns:
            The static file URL
        """
        return f"{self.static_url}/{filename.lstrip('/')}"


class DevelopmentStaticFilesMiddleware(StaticFilesMiddleware):
    """
    Middleware for serving static files in development mode.
    
    This middleware provides additional features for development,
    such as automatic reloading and better error messages.
    """
    
    def __init__(self, app, static_url: str = "/static/", static_dirs: List[str] = None,
                 debug: bool = True):
        """
        Initialize the development static files middleware.
        
        Args:
            app: The FastAPI app
            static_url: URL prefix for static files
            static_dirs: List of static directories to search
            debug: Whether to enable debug features
        """
        super().__init__(app, static_url, static_dirs)
        self.debug = debug
    
    async def _serve_static_file(self, request: Request) -> Response:
        """
        Serve a static file with development features.
        
        Args:
            request: The request object
            
        Returns:
            FileResponse or detailed error response
        """
        try:
            return await super()._serve_static_file(request)
        except HTTPException as e:
            if self.debug and e.status_code == 404:
                # Provide detailed error information in development
                return await self._create_debug_response(request, e)
            raise
    
    async def _create_debug_response(self, request: Request, exception: HTTPException) -> Response:
        """
        Create a debug response for missing static files.
        
        Args:
            request: The request object
            exception: The HTTP exception
            
        Returns:
            HTML response with debug information
        """
        url_path = request.url.path
        file_path = url_path[len(self.static_url):].lstrip('/')
        
        # List available static files
        available_files = []
        for static_dir in self.static_dirs:
            static_path = Path(static_dir)
            if static_path.exists():
                for file in static_path.rglob('*'):
                    if file.is_file():
                        rel_path = file.relative_to(static_path)
                        available_files.append(str(rel_path))
        
        # Create debug HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Static File Not Found</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ color: #d32f2f; }}
                .info {{ color: #1976d2; }}
                .file-list {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
                .file-item {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
            <h1 class="error">Static File Not Found</h1>
            <p><strong>Requested file:</strong> {file_path}</p>
            <p><strong>Static URL:</strong> {self.static_url}</p>
            <p><strong>Static directories:</strong></p>
            <ul>
                {''.join(f'<li>{static_dir}</li>' for static_dir in self.static_dirs)}
            </ul>
            
            <h2>Available Static Files:</h2>
            <div class="file-list">
                {''.join(f'<div class="file-item">{file}</div>' for file in sorted(available_files)[:50])}
                {f'<div class="info">... and {len(available_files) - 50} more files</div>' if len(available_files) > 50 else ''}
            </div>
            
            <p class="info">This is a development-only error page. In production, static files should be served by a web server.</p>
        </body>
        </html>
        """
        
        return Response(
            content=html_content,
            media_type="text/html",
            status_code=404
        )


# Example usage:
def setup_static_middleware(app, settings: Dict[str, Any]):
    """
    Set up static files middleware using Django-like settings.
    
    Args:
        app: The FastAPI app
        settings: Settings dictionary with static file configuration
    """
    static_url = settings.get('STATIC_URL', '/static/')
    staticfiles_dirs = settings.get('STATICFILES_DIRS', [])
    debug = settings.get('DEBUG', False)
    
    if debug:
        # Development mode: use development middleware
        middleware = DevelopmentStaticFilesMiddleware(
            app,
            static_url=static_url,
            static_dirs=staticfiles_dirs or ["static"],
            debug=debug
        )
    else:
        # Production mode: use standard middleware
        middleware = StaticFilesMiddleware(
            app,
            static_url=static_url,
            static_dirs=staticfiles_dirs or ["static"]
        )
    
    # Add middleware to app
    app.add_middleware(type(middleware), **middleware.__dict__)