"""
FastJango Authentication Middleware - Django-like authentication.

This module provides authentication middleware for FastJango, similar to Django's
authentication middleware but adapted for FastAPI.
"""

import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError
from fastjango.middleware.session import get_session_data, set_session_data


@dataclass
class User:
    """Simple user model for authentication."""
    
    id: int
    username: str
    email: str
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    date_joined: Optional[str] = None
    last_login: Optional[str] = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.is_active
    
    def has_perm(self, perm: str) -> bool:
        """Check if user has permission."""
        if self.is_superuser:
            return True
        return False  # Simplified for now
    
    def has_module_perms(self, app_label: str) -> bool:
        """Check if user has module permissions."""
        if self.is_superuser:
            return True
        return False  # Simplified for now


class AuthenticationBackend:
    """Base class for authentication backends."""
    
    def authenticate(self, request: Request, **credentials) -> Optional[User]:
        """Authenticate a user."""
        raise NotImplementedError
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        raise NotImplementedError


class SessionAuthenticationBackend(AuthenticationBackend):
    """Session-based authentication backend."""
    
    def authenticate(self, request: Request, **credentials) -> Optional[User]:
        """Authenticate using session."""
        user_id = get_session_data(request, 'user_id')
        if user_id:
            return self.get_user(user_id)
        return None
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID from session."""
        # This is a simplified implementation
        # In a real app, you'd query the database
        if user_id == 1:
            return User(
                id=1,
                username="admin",
                email="admin@example.com",
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
        return None


class TokenAuthenticationBackend(AuthenticationBackend):
    """Token-based authentication backend."""
    
    def __init__(self, token_header: str = "Authorization"):
        self.token_header = token_header
    
    def authenticate(self, request: Request, **credentials) -> Optional[User]:
        """Authenticate using token."""
        auth_header = request.headers.get(self.token_header)
        if not auth_header:
            return None
        
        # Extract token from "Bearer <token>" format
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = auth_header
        
        # Validate token (simplified)
        if token == "valid_token":
            return User(
                id=1,
                username="token_user",
                email="token@example.com",
                is_active=True
            )
        return None
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return SessionAuthenticationBackend().get_user(user_id)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Django-like authentication middleware for FastJango.
    
    This middleware provides authentication similar to Django's
    authentication middleware, with support for multiple backends.
    """
    
    def __init__(self, app,
                 backends: Optional[list] = None,
                 session_backend: Optional[AuthenticationBackend] = None,
                 token_backend: Optional[AuthenticationBackend] = None):
        """
        Initialize the authentication middleware.
        
        Args:
            app: The FastAPI application
            backends: List of authentication backends
            session_backend: Session authentication backend
            token_backend: Token authentication backend
        """
        super().__init__(app)
        
        self.backends = backends or []
        self.session_backend = session_backend or SessionAuthenticationBackend()
        self.token_backend = token_backend or TokenAuthenticationBackend()
        
        # Add default backends if none provided
        if not self.backends:
            self.backends = [self.session_backend, self.token_backend]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through authentication middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Try to authenticate user
        user = None
        
        for backend in self.backends:
            try:
                user = backend.authenticate(request)
                if user:
                    break
            except Exception:
                continue
        
        # Attach user to request
        request.state.user = user
        
        # Process request
        response = await call_next(request)
        
        return response


def get_user(request: Request) -> Optional[User]:
    """
    Get the current user from request.
    
    Args:
        request: The request object
        
    Returns:
        User object or None
    """
    return getattr(request.state, 'user', None)


def get_user_id(request: Request) -> Optional[int]:
    """
    Get the current user ID from request.
    
    Args:
        request: The request object
        
    Returns:
        User ID or None
    """
    user = get_user(request)
    return user.id if user else None


def is_authenticated(request: Request) -> bool:
    """
    Check if user is authenticated.
    
    Args:
        request: The request object
        
    Returns:
        True if user is authenticated
    """
    user = get_user(request)
    return user is not None and user.is_authenticated()


def login(request: Request, user: User) -> None:
    """
    Log in a user.
    
    Args:
        request: The request object
        user: The user to log in
    """
    set_session_data(request, 'user_id', user.id)
    set_session_data(request, 'user_username', user.username)
    set_session_data(request, 'user_email', user.email)
    set_session_data(request, 'user_is_staff', user.is_staff)
    set_session_data(request, 'user_is_superuser', user.is_superuser)
    set_session_data(request, 'user_last_login', time.time())


def logout(request: Request) -> None:
    """
    Log out the current user.
    
    Args:
        request: The request object
    """
    from fastjango.middleware.session import clear_session
    clear_session(request)


def login_required(func: Callable) -> Callable:
    """
    Decorator to require authentication.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    async def wrapper(request: Request, *args, **kwargs):
        if not is_authenticated(request):
            from fastjango.http import HttpResponse
            return HttpResponse("Authentication required", status_code=401)
        return await func(request, *args, **kwargs)
    
    return wrapper


def staff_member_required(func: Callable) -> Callable:
    """
    Decorator to require staff membership.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    async def wrapper(request: Request, *args, **kwargs):
        user = get_user(request)
        if not user or not user.is_staff:
            from fastjango.http import HttpResponse
            return HttpResponse("Staff access required", status_code=403)
        return await func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(func: Callable) -> Callable:
    """
    Decorator to require superuser status.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    async def wrapper(request: Request, *args, **kwargs):
        user = get_user(request)
        if not user or not user.is_superuser:
            from fastjango.http import HttpResponse
            return HttpResponse("Superuser access required", status_code=403)
        return await func(request, *args, **kwargs)
    
    return wrapper


def permission_required(perm: str) -> Callable:
    """
    Decorator to require specific permission.
    
    Args:
        perm: The permission to require
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            user = get_user(request)
            if not user or not user.has_perm(perm):
                from fastjango.http import HttpResponse
                return HttpResponse("Permission required", status_code=403)
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
