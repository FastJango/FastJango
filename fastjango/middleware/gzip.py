"""
FastJango GZip Middleware - Django-like response compression.

This module provides GZip middleware for FastJango, similar to Django's
GZip middleware but adapted for FastAPI.
"""

import gzip
import io
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError


class GZipMiddleware(BaseHTTPMiddleware):
    """
    Django-like GZip middleware for FastJango.
    
    This middleware provides response compression similar to Django's
    GZip middleware, with support for various compression options.
    """
    
    def __init__(self, app,
                 compress_level: int = 6,
                 min_size: int = 200,
                 content_types: Optional[List[str]] = None,
                 exclude_paths: Optional[List[str]] = None,
                 include_paths: Optional[List[str]] = None):
        """
        Initialize the GZip middleware.
        
        Args:
            app: The FastAPI application
            compress_level: GZip compression level (1-9)
            min_size: Minimum response size to compress
            content_types: Content types to compress
            exclude_paths: Paths to exclude from compression
            include_paths: Paths to include in compression
        """
        super().__init__(app)
        
        self.compress_level = max(1, min(9, compress_level))
        self.min_size = min_size
        self.content_types = content_types or [
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
            "text/xml",
            "text/plain"
        ]
        self.exclude_paths = exclude_paths or []
        self.include_paths = include_paths or []
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed."""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False
        
        # Check response size
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.min_size:
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type.lower() for ct in self.content_types):
            return False
        
        # Check path exclusions
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # Check path inclusions (if specified)
        if self.include_paths:
            for include_path in self.include_paths:
                if path.startswith(include_path):
                    return True
            return False
        
        return True
    
    def _compress_content(self, content: bytes) -> bytes:
        """Compress content using gzip."""
        buffer = io.BytesIO()
        
        with gzip.GzipFile(mode='wb', fileobj=buffer, compresslevel=self.compress_level) as gz:
            gz.write(content)
        
        return buffer.getvalue()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through GZip middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Process request
        response = await call_next(request)
        
        # Check if we should compress
        if not self._should_compress(request, response):
            return response
        
        # Get response content
        if hasattr(response, 'body'):
            content = response.body
        else:
            # For streaming responses, we can't compress
            return response
        
        # Compress content
        compressed_content = self._compress_content(content)
        
        # Update response
        response.body = compressed_content
        response.headers["content-encoding"] = "gzip"
        response.headers["content-length"] = str(len(compressed_content))
        
        return response


class DeflateMiddleware(BaseHTTPMiddleware):
    """
    Deflate compression middleware.
    
    This middleware provides deflate compression for responses.
    """
    
    def __init__(self, app,
                 compress_level: int = 6,
                 min_size: int = 200,
                 content_types: Optional[List[str]] = None):
        """
        Initialize the deflate middleware.
        
        Args:
            app: The FastAPI application
            compress_level: Deflate compression level (1-9)
            min_size: Minimum response size to compress
            content_types: Content types to compress
        """
        super().__init__(app)
        
        self.compress_level = max(1, min(9, compress_level))
        self.min_size = min_size
        self.content_types = content_types or [
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json"
        ]
    
    def _should_compress(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed."""
        # Check if client accepts deflate
        accept_encoding = request.headers.get("accept-encoding", "")
        if "deflate" not in accept_encoding.lower():
            return False
        
        # Check response size
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.min_size:
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type.lower() for ct in self.content_types):
            return False
        
        return True
    
    def _compress_content(self, content: bytes) -> bytes:
        """Compress content using deflate."""
        import zlib
        
        compressor = zlib.compressobj(self.compress_level)
        compressed = compressor.compress(content)
        compressed += compressor.flush()
        
        return compressed
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through deflate middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Process request
        response = await call_next(request)
        
        # Check if we should compress
        if not self._should_compress(request, response):
            return response
        
        # Get response content
        if hasattr(response, 'body'):
            content = response.body
        else:
            # For streaming responses, we can't compress
            return response
        
        # Compress content
        compressed_content = self._compress_content(content)
        
        # Update response
        response.body = compressed_content
        response.headers["content-encoding"] = "deflate"
        response.headers["content-length"] = str(len(compressed_content))
        
        return response


def setup_compression_middleware(app, settings: Dict[str, Any]):
    """
    Set up compression middleware using Django-like settings.
    
    Args:
        app: The FastAPI application
        settings: Settings dictionary
    """
    # GZip middleware
    if settings.get("USE_GZIP", True):
        gzip_middleware = GZipMiddleware(
            app,
            compress_level=settings.get("GZIP_COMPRESS_LEVEL", 6),
            min_size=settings.get("GZIP_MIN_SIZE", 200),
            content_types=settings.get("GZIP_CONTENT_TYPES", []),
            exclude_paths=settings.get("GZIP_EXCLUDE_PATHS", []),
            include_paths=settings.get("GZIP_INCLUDE_PATHS", [])
        )
        app.add_middleware(GZipMiddleware, **gzip_middleware.__dict__)
    
    # Deflate middleware
    if settings.get("USE_DEFLATE", False):
        deflate_middleware = DeflateMiddleware(
            app,
            compress_level=settings.get("DEFLATE_COMPRESS_LEVEL", 6),
            min_size=settings.get("DEFLATE_MIN_SIZE", 200),
            content_types=settings.get("DEFLATE_CONTENT_TYPES", [])
        )
        app.add_middleware(DeflateMiddleware, **deflate_middleware.__dict__)
