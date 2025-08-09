"""
FastJango Common Middleware - Django-like common HTTP middleware.

This module provides common middleware for FastJango, similar to Django's
common middleware but adapted for FastAPI.
"""

import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError


class CommonMiddleware(BaseHTTPMiddleware):
    """
    Django-like common middleware for FastJango.
    
    This middleware provides common HTTP features similar to Django's
    common middleware, including request processing and response handling.
    """
    
    def __init__(self, app,
                 append_slash: bool = True,
                 remove_trailing_slash: bool = False,
                 ignore_paths: Optional[List[str]] = None,
                 process_request: bool = True,
                 process_response: bool = True,
                 process_exception: bool = True):
        """
        Initialize the common middleware.
        
        Args:
            app: The FastAPI application
            append_slash: Whether to append trailing slash
            remove_trailing_slash: Whether to remove trailing slash
            ignore_paths: Paths to ignore for slash handling
            process_request: Whether to process requests
            process_response: Whether to process responses
            process_exception: Whether to process exceptions
        """
        super().__init__(app)
        
        self.append_slash = append_slash
        self.remove_trailing_slash = remove_trailing_slash
        self.ignore_paths = ignore_paths or []
        self.process_request = process_request
        self.process_response = process_response
        self.process_exception = process_exception
    
    def _should_ignore_path(self, path: str) -> bool:
        """Check if path should be ignored."""
        for ignore_path in self.ignore_paths:
            if path.startswith(ignore_path):
                return True
        return False
    
    def _should_append_slash(self, path: str) -> bool:
        """Check if slash should be appended."""
        if not self.append_slash:
            return False
        
        if self._should_ignore_path(path):
            return False
        
        # Don't append slash to files or API endpoints
        if "." in path.split("/")[-1] or path.startswith("/api/"):
            return False
        
        return not path.endswith("/")
    
    def _should_remove_slash(self, path: str) -> bool:
        """Check if slash should be removed."""
        if not self.remove_trailing_slash:
            return False
        
        if self._should_ignore_path(path):
            return False
        
        return path.endswith("/") and len(path) > 1
    
    def _get_redirect_url(self, request: Request, new_path: str) -> str:
        """Get redirect URL for path changes."""
        url = request.url
        return f"{url.scheme}://{url.netloc}{new_path}{url.query}"
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through common middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        path = request.url.path
        
        # Handle slash appending/removing
        if self.append_slash and self._should_append_slash(path):
            new_path = path + "/"
            redirect_url = self._get_redirect_url(request, new_path)
            from fastjango.http import redirect
            return redirect(redirect_url, permanent=True)
        
        if self.remove_trailing_slash and self._should_remove_slash(path):
            new_path = path.rstrip("/")
            redirect_url = self._get_redirect_url(request, new_path)
            from fastjango.http import redirect
            return redirect(redirect_url, permanent=True)
        
        # Process request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            if self.process_exception:
                # Handle exceptions
                from fastjango.http import HttpResponse
                return HttpResponse(f"Internal server error: {str(e)}", status_code=500)
            raise


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware.
    
    This middleware logs request information for debugging and monitoring.
    """
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        """
        Initialize the request logging middleware.
        
        Args:
            app: The FastAPI application
            log_requests: Whether to log requests
            log_responses: Whether to log responses
        """
        super().__init__(app)
        
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through logging middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        start_time = time.time()
        
        # Log request
        if self.log_requests:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        if self.log_responses:
            duration = time.time() - start_time
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Request ID middleware.
    
    This middleware adds a unique request ID to each request for tracking.
    """
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        """
        Initialize the request ID middleware.
        
        Args:
            app: The FastAPI application
            header_name: Name of the request ID header
        """
        super().__init__(app)
        
        self.header_name = header_name
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through request ID middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Get or generate request ID
        request_id = request.headers.get(self.header_name) or self._generate_request_id()
        
        # Attach to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[self.header_name] = request_id
        
        return response


def setup_common_middleware(app, settings: Dict[str, Any]):
    """
    Set up common middleware using Django-like settings.
    
    Args:
        app: The FastAPI application
        settings: Settings dictionary
    """
    # Common middleware
    common_middleware = CommonMiddleware(
        app,
        append_slash=settings.get("APPEND_SLASH", True),
        remove_trailing_slash=settings.get("REMOVE_TRAILING_SLASH", False),
        ignore_paths=settings.get("COMMON_IGNORE_PATHS", []),
        process_request=settings.get("COMMON_PROCESS_REQUEST", True),
        process_response=settings.get("COMMON_PROCESS_RESPONSE", True),
        process_exception=settings.get("COMMON_PROCESS_EXCEPTION", True)
    )
    
    app.add_middleware(CommonMiddleware, **common_middleware.__dict__)
    
    # Request logging middleware
    if settings.get("LOG_REQUESTS", False):
        logging_middleware = RequestLoggingMiddleware(
            app,
            log_requests=settings.get("LOG_REQUESTS", True),
            log_responses=settings.get("LOG_RESPONSES", True)
        )
        app.add_middleware(RequestLoggingMiddleware, **logging_middleware.__dict__)
    
    # Request ID middleware
    if settings.get("USE_REQUEST_ID", False):
        request_id_middleware = RequestIDMiddleware(
            app,
            header_name=settings.get("REQUEST_ID_HEADER", "X-Request-ID")
        )
        app.add_middleware(RequestIDMiddleware, **request_id_middleware.__dict__)
