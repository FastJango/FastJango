"""
FastJango CORS Middleware - Django-like CORS handling.

This module provides CORS middleware for FastJango, similar to Django's
CORS middleware but adapted for FastAPI.
"""

from typing import List, Optional, Union, Dict, Any
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError
from fastjango.core.settings import get_settings_instance, get_cors_settings


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Django-like CORS middleware for FastJango.
    
    This middleware provides CORS handling similar to Django's
    CORS middleware, with support for various CORS policies.
    """
    
    def __init__(self, app,
                 allowed_origins: Optional[List[str]] = None,
                 allowed_origin_regexes: Optional[List[str]] = None,
                 allowed_methods: Optional[List[str]] = None,
                 allowed_headers: Optional[List[str]] = None,
                 exposed_headers: Optional[List[str]] = None,
                 allow_credentials: bool = False,
                 max_age: Optional[int] = None,
                 allow_all_origins: bool = False,
                 allow_all_methods: bool = False,
                 allow_all_headers: bool = False):
        """
        Initialize the CORS middleware.
        
        Args:
            app: The FastAPI application
            allowed_origins: List of allowed origins
            allowed_origin_regexes: List of allowed origin regexes
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed headers
            exposed_headers: List of exposed headers
            allow_credentials: Whether to allow credentials
            max_age: CORS preflight cache time
            allow_all_origins: Whether to allow all origins
            allow_all_methods: Whether to allow all methods
            allow_all_headers: Whether to allow all headers
        """
        super().__init__(app)
        
        # Get settings if not provided
        settings = get_settings_instance()
        cors_settings = get_cors_settings(settings)
        
        self.allowed_origins = allowed_origins or cors_settings['allowed_origins']
        self.allowed_origin_regexes = allowed_origin_regexes or cors_settings['allowed_origin_regexes']
        self.allowed_methods = allowed_methods or cors_settings['allowed_methods']
        self.allowed_headers = allowed_headers or cors_settings['allowed_headers']
        self.exposed_headers = exposed_headers or cors_settings['exposed_headers']
        self.allow_credentials = allow_credentials or cors_settings['allow_credentials']
        self.max_age = max_age or cors_settings['max_age']
        self.allow_all_origins = allow_all_origins or cors_settings['allow_all_origins']
        self.allow_all_methods = allow_all_methods or cors_settings['allow_all_methods']
        self.allow_all_headers = allow_all_headers or cors_settings['allow_all_headers']
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if self.allow_all_origins:
            return True
        
        # Check exact matches
        if origin in self.allowed_origins:
            return True
        
        # Check regex matches
        import re
        for pattern in self.allowed_origin_regexes:
            if re.match(pattern, origin):
                return True
        
        return False
    
    def _is_method_allowed(self, method: str) -> bool:
        """Check if method is allowed."""
        if self.allow_all_methods:
            return True
        
        return method.upper() in [m.upper() for m in self.allowed_methods]
    
    def _is_header_allowed(self, header: str) -> bool:
        """Check if header is allowed."""
        if self.allow_all_headers:
            return True
        
        return header.lower() in [h.lower() for h in self.allowed_headers]
    
    def _get_origin(self, request: Request) -> Optional[str]:
        """Get origin from request."""
        return request.headers.get("origin")
    
    def _get_request_method(self, request: Request) -> str:
        """Get request method."""
        return request.method.upper()
    
    def _get_request_headers(self, request: Request) -> List[str]:
        """Get request headers."""
        access_control_request_headers = request.headers.get("access-control-request-headers", "")
        if access_control_request_headers:
            return [h.strip() for h in access_control_request_headers.split(",")]
        return []
    
    def _add_cors_headers(self, response: Response, origin: str, request_method: str = None) -> None:
        """Add CORS headers to response."""
        # Access-Control-Allow-Origin
        if self.allow_all_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Access-Control-Allow-Methods
        if self.allow_all_methods:
            response.headers["Access-Control-Allow-Methods"] = "*"
        else:
            methods = ", ".join(self.allowed_methods)
            response.headers["Access-Control-Allow-Methods"] = methods
        
        # Access-Control-Allow-Headers
        if self.allow_all_headers:
            response.headers["Access-Control-Allow-Headers"] = "*"
        elif self.allowed_headers:
            headers = ", ".join(self.allowed_headers)
            response.headers["Access-Control-Allow-Headers"] = headers
        
        # Access-Control-Expose-Headers
        if self.exposed_headers:
            headers = ", ".join(self.exposed_headers)
            response.headers["Access-Control-Expose-Headers"] = headers
        
        # Access-Control-Allow-Credentials
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Access-Control-Max-Age
        if self.max_age:
            response.headers["Access-Control-Max-Age"] = str(self.max_age)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through CORS middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        origin = self._get_origin(request)
        method = self._get_request_method(request)
        
        # Handle preflight requests
        if method == "OPTIONS":
            if not origin or not self._is_origin_allowed(origin):
                from fastjango.http import HttpResponse
                return HttpResponse("CORS not allowed", status_code=400)
            
            # Check request method
            request_method = request.headers.get("access-control-request-method", "").upper()
            if request_method and not self._is_method_allowed(request_method):
                from fastjango.http import HttpResponse
                return HttpResponse("Method not allowed", status_code=400)
            
            # Check request headers
            request_headers = self._get_request_headers(request)
            for header in request_headers:
                if not self._is_header_allowed(header):
                    from fastjango.http import HttpResponse
                    return HttpResponse("Header not allowed", status_code=400)
            
            # Return preflight response
            response = Response()
            self._add_cors_headers(response, origin, request_method)
            return response
        
        # Handle actual requests
        if origin and not self._is_origin_allowed(origin):
            from fastjango.http import HttpResponse
            return HttpResponse("CORS not allowed", status_code=400)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin:
            self._add_cors_headers(response, origin, method)
        
        return response


def setup_cors_middleware(app, **kwargs):
    """
    Set up CORS middleware using Django-like settings.
    
    Args:
        app: The FastAPI application
        **kwargs: CORS settings to override defaults
    """
    # Get settings
    settings = get_settings_instance()
    cors_settings = get_cors_settings(settings)
    
    # Override with kwargs if provided
    allowed_origins = kwargs.get('allowed_origins', cors_settings['allowed_origins'])
    allowed_origin_regexes = kwargs.get('allowed_origin_regexes', cors_settings['allowed_origin_regexes'])
    allowed_methods = kwargs.get('allowed_methods', cors_settings['allowed_methods'])
    allowed_headers = kwargs.get('allowed_headers', cors_settings['allowed_headers'])
    exposed_headers = kwargs.get('exposed_headers', cors_settings['exposed_headers'])
    allow_credentials = kwargs.get('allow_credentials', cors_settings['allow_credentials'])
    max_age = kwargs.get('max_age', cors_settings['max_age'])
    allow_all_origins = kwargs.get('allow_all_origins', cors_settings['allow_all_origins'])
    allow_all_methods = kwargs.get('allow_all_methods', cors_settings['allow_all_methods'])
    allow_all_headers = kwargs.get('allow_all_headers', cors_settings['allow_all_headers'])
    
    cors_middleware = CORSMiddleware(
        app,
        allowed_origins=allowed_origins,
        allowed_origin_regexes=allowed_origin_regexes,
        allowed_methods=allowed_methods,
        allowed_headers=allowed_headers,
        exposed_headers=exposed_headers,
        allow_credentials=allow_credentials,
        max_age=max_age,
        allow_all_origins=allow_all_origins,
        allow_all_methods=allow_all_methods,
        allow_all_headers=allow_all_headers
    )
    
    app.add_middleware(CORSMiddleware, **cors_middleware.__dict__)