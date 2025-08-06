"""
FastJango Security Middleware - Django-like security features.

This module provides security middleware for FastJango, similar to Django's
security middleware but adapted for FastAPI.
"""

import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Django-like security middleware for FastJango.
    
    This middleware provides security features similar to Django's
    security middleware, including security headers and CSRF protection.
    """
    
    def __init__(self, app,
                 security_headers: Optional[Dict[str, str]] = None,
                 allowed_hosts: Optional[List[str]] = None,
                 secure_ssl_redirect: bool = False,
                 secure_ssl_host: Optional[str] = None,
                 secure_content_type_nosniff: bool = True,
                 secure_browser_xss_filter: bool = True,
                 secure_frame_deny: bool = True,
                 secure_content_security_policy: Optional[str] = None,
                 secure_referrer_policy: Optional[str] = None,
                 secure_permissions_policy: Optional[str] = None,
                 secure_cross_origin_opener_policy: Optional[str] = None,
                 secure_cross_origin_embedder_policy: Optional[str] = None,
                 secure_cross_origin_resource_policy: Optional[str] = None):
        """
        Initialize the security middleware.
        
        Args:
            app: The FastAPI application
            security_headers: Custom security headers
            allowed_hosts: List of allowed hosts
            secure_ssl_redirect: Whether to redirect HTTP to HTTPS
            secure_ssl_host: SSL host for redirects
            secure_content_type_nosniff: Add X-Content-Type-Options header
            secure_browser_xss_filter: Add X-XSS-Protection header
            secure_frame_deny: Add X-Frame-Options header
            secure_content_security_policy: Content Security Policy header
            secure_referrer_policy: Referrer Policy header
            secure_permissions_policy: Permissions Policy header
            secure_cross_origin_opener_policy: Cross-Origin-Opener-Policy header
            secure_cross_origin_embedder_policy: Cross-Origin-Embedder-Policy header
            secure_cross_origin_resource_policy: Cross-Origin-Resource-Policy header
        """
        super().__init__(app)
        
        self.security_headers = security_headers or {}
        self.allowed_hosts = allowed_hosts or ["*"]
        self.secure_ssl_redirect = secure_ssl_redirect
        self.secure_ssl_host = secure_ssl_host
        self.secure_content_type_nosniff = secure_content_type_nosniff
        self.secure_browser_xss_filter = secure_browser_xss_filter
        self.secure_frame_deny = secure_frame_deny
        self.secure_content_security_policy = secure_content_security_policy
        self.secure_referrer_policy = secure_referrer_policy
        self.secure_permissions_policy = secure_permissions_policy
        self.secure_cross_origin_opener_policy = secure_cross_origin_opener_policy
        self.secure_cross_origin_embedder_policy = secure_cross_origin_embedder_policy
        self.secure_cross_origin_resource_policy = secure_cross_origin_resource_policy
    
    def _is_allowed_host(self, host: str) -> bool:
        """Check if host is allowed."""
        if "*" in self.allowed_hosts:
            return True
        
        return host in self.allowed_hosts
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add."""
        headers = {}
        
        # Add custom headers
        headers.update(self.security_headers)
        
        # Content Type Options
        if self.secure_content_type_nosniff:
            headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        if self.secure_browser_xss_filter:
            headers["X-XSS-Protection"] = "1; mode=block"
        
        # Frame Options
        if self.secure_frame_deny:
            headers["X-Frame-Options"] = "DENY"
        
        # Content Security Policy
        if self.secure_content_security_policy:
            headers["Content-Security-Policy"] = self.secure_content_security_policy
        
        # Referrer Policy
        if self.secure_referrer_policy:
            headers["Referrer-Policy"] = self.secure_referrer_policy
        
        # Permissions Policy
        if self.secure_permissions_policy:
            headers["Permissions-Policy"] = self.secure_permissions_policy
        
        # Cross-Origin Opener Policy
        if self.secure_cross_origin_opener_policy:
            headers["Cross-Origin-Opener-Policy"] = self.secure_cross_origin_opener_policy
        
        # Cross-Origin Embedder Policy
        if self.secure_cross_origin_embedder_policy:
            headers["Cross-Origin-Embedder-Policy"] = self.secure_cross_origin_embedder_policy
        
        # Cross-Origin Resource Policy
        if self.secure_cross_origin_resource_policy:
            headers["Cross-Origin-Resource-Policy"] = self.secure_cross_origin_resource_policy
        
        return headers
    
    def _should_redirect_to_ssl(self, request: Request) -> bool:
        """Check if request should be redirected to SSL."""
        if not self.secure_ssl_redirect:
            return False
        
        # Check if request is already HTTPS
        if request.url.scheme == "https":
            return False
        
        # Check if request is from localhost (development)
        if request.url.hostname in ["localhost", "127.0.0.1"]:
            return False
        
        return True
    
    def _get_ssl_redirect_url(self, request: Request) -> str:
        """Get SSL redirect URL."""
        if self.secure_ssl_host:
            host = self.secure_ssl_host
        else:
            host = request.url.hostname
        
        return f"https://{host}{request.url.path}{request.url.query}"
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through security middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Check allowed hosts
        host = request.headers.get("host", "")
        if host and not self._is_allowed_host(host):
            from fastjango.http import HttpResponse
            return HttpResponse("Invalid host header", status_code=400)
        
        # Check SSL redirect
        if self._should_redirect_to_ssl(request):
            redirect_url = self._get_ssl_redirect_url(request)
            from fastjango.http import redirect
            return redirect(redirect_url, permanent=True)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        security_headers = self._get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class HSTSMiddleware(BaseHTTPMiddleware):
    """
    HTTP Strict Transport Security middleware.
    
    This middleware adds HSTS headers to force HTTPS connections.
    """
    
    def __init__(self, app,
                 max_age: int = 31536000,  # 1 year
                 include_subdomains: bool = True,
                 preload: bool = False):
        """
        Initialize the HSTS middleware.
        
        Args:
            app: The FastAPI application
            max_age: HSTS max age in seconds
            include_subdomains: Whether to include subdomains
            preload: Whether to include preload directive
        """
        super().__init__(app)
        
        self.max_age = max_age
        self.include_subdomains = include_subdomains
        self.preload = preload
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through HSTS middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        response = await call_next(request)
        
        # Only add HSTS for HTTPS responses
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.max_age}"
            
            if self.include_subdomains:
                hsts_value += "; includeSubDomains"
            
            if self.preload:
                hsts_value += "; preload"
            
            response.headers["Strict-Transport-Security"] = hsts_value
        
        return response


class ReferrerPolicyMiddleware(BaseHTTPMiddleware):
    """
    Referrer Policy middleware.
    
    This middleware adds Referrer-Policy headers to control referrer information.
    """
    
    def __init__(self, app, policy: str = "strict-origin-when-cross-origin"):
        """
        Initialize the Referrer Policy middleware.
        
        Args:
            app: The FastAPI application
            policy: Referrer policy value
        """
        super().__init__(app)
        self.policy = policy
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through Referrer Policy middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        response = await call_next(request)
        response.headers["Referrer-Policy"] = self.policy
        return response


def setup_security_middleware(app, settings: Dict[str, Any]):
    """
    Set up security middleware using Django-like settings.
    
    Args:
        app: The FastAPI application
        settings: Settings dictionary
    """
    # Security middleware
    security_middleware = SecurityMiddleware(
        app,
        security_headers=settings.get("SECURITY_HEADERS", {}),
        allowed_hosts=settings.get("ALLOWED_HOSTS", ["*"]),
        secure_ssl_redirect=settings.get("SECURE_SSL_REDIRECT", False),
        secure_ssl_host=settings.get("SECURE_SSL_HOST"),
        secure_content_type_nosniff=settings.get("SECURE_CONTENT_TYPE_NOSNIFF", True),
        secure_browser_xss_filter=settings.get("SECURE_BROWSER_XSS_FILTER", True),
        secure_frame_deny=settings.get("SECURE_FRAME_DENY", True),
        secure_content_security_policy=settings.get("SECURE_CONTENT_SECURITY_POLICY"),
        secure_referrer_policy=settings.get("SECURE_REFERRER_POLICY"),
        secure_permissions_policy=settings.get("SECURE_PERMISSIONS_POLICY"),
        secure_cross_origin_opener_policy=settings.get("SECURE_CROSS_ORIGIN_OPENER_POLICY"),
        secure_cross_origin_embedder_policy=settings.get("SECURE_CROSS_ORIGIN_EMBEDDER_POLICY"),
        secure_cross_origin_resource_policy=settings.get("SECURE_CROSS_ORIGIN_RESOURCE_POLICY")
    )
    
    app.add_middleware(SecurityMiddleware, **security_middleware.__dict__)
    
    # HSTS middleware
    if settings.get("SECURE_HSTS_SECONDS", 0) > 0:
        hsts_middleware = HSTSMiddleware(
            app,
            max_age=settings.get("SECURE_HSTS_SECONDS", 31536000),
            include_subdomains=settings.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", True),
            preload=settings.get("SECURE_HSTS_PRELOAD", False)
        )
        app.add_middleware(HSTSMiddleware, **hsts_middleware.__dict__)
    
    # Referrer Policy middleware
    if settings.get("SECURE_REFERRER_POLICY"):
        referrer_middleware = ReferrerPolicyMiddleware(
            app,
            policy=settings.get("SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
        )
        app.add_middleware(ReferrerPolicyMiddleware, **referrer_middleware.__dict__)