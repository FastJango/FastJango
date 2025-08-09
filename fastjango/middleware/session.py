"""
FastJango Session Middleware - Django-like session management.

This module provides session middleware for FastJango, similar to Django's
session middleware but adapted for FastAPI.
"""

import json
import time
import secrets
from typing import Dict, Any, Optional
from pathlib import Path
import pickle
import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import State

from fastjango.core.exceptions import FastJangoError


class SessionStore:
    """Base class for session storage backends."""
    
    def get(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get session data by key."""
        raise NotImplementedError
    
    def set(self, session_key: str, data: Dict[str, Any], expiry: int) -> None:
        """Set session data with expiry."""
        raise NotImplementedError
    
    def delete(self, session_key: str) -> None:
        """Delete session data."""
        raise NotImplementedError
    
    def exists(self, session_key: str) -> bool:
        """Check if session exists."""
        raise NotImplementedError


class FileSessionStore(SessionStore):
    """File-based session storage."""
    
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
    
    def _get_session_path(self, session_key: str) -> Path:
        """Get the file path for a session key."""
        return self.session_dir / f"{session_key}.session"
    
    def get(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get session data from file."""
        session_path = self._get_session_path(session_key)
        
        if not session_path.exists():
            return None
        
        try:
            with open(session_path, 'rb') as f:
                data = pickle.load(f)
                
            # Check expiry
            if data.get('expiry', 0) < time.time():
                self.delete(session_key)
                return None
                
            return data.get('data', {})
        except Exception:
            return None
    
    def set(self, session_key: str, data: Dict[str, Any], expiry: int) -> None:
        """Set session data to file."""
        session_path = self._get_session_path(session_key)
        
        session_data = {
            'data': data,
            'expiry': expiry,
            'created': time.time()
        }
        
        try:
            with open(session_path, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            raise FastJangoError(f"Failed to save session: {e}")
    
    def delete(self, session_key: str) -> None:
        """Delete session file."""
        session_path = self._get_session_path(session_key)
        if session_path.exists():
            session_path.unlink()
    
    def exists(self, session_key: str) -> bool:
        """Check if session file exists."""
        session_path = self._get_session_path(session_key)
        return session_path.exists()


class MemorySessionStore(SessionStore):
    """In-memory session storage."""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def get(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get session data from memory."""
        if session_key not in self._sessions:
            return None
        
        session_data = self._sessions[session_key]
        
        # Check expiry
        if session_data.get('expiry', 0) < time.time():
            self.delete(session_key)
            return None
        
        return session_data.get('data', {})
    
    def set(self, session_key: str, data: Dict[str, Any], expiry: int) -> None:
        """Set session data in memory."""
        self._sessions[session_key] = {
            'data': data,
            'expiry': expiry,
            'created': time.time()
        }
    
    def delete(self, session_key: str) -> None:
        """Delete session from memory."""
        self._sessions.pop(session_key, None)
    
    def exists(self, session_key: str) -> bool:
        """Check if session exists in memory."""
        return session_key in self._sessions


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Django-like session middleware for FastJango.
    
    This middleware provides session management similar to Django's
    session middleware, with support for different storage backends.
    """
    
    def __init__(self, app, 
                 session_store: Optional[SessionStore] = None,
                 session_cookie_name: str = "sessionid",
                 session_cookie_age: int = 1209600,  # 2 weeks
                 session_cookie_domain: Optional[str] = None,
                 session_cookie_secure: bool = False,
                 session_cookie_httponly: bool = True,
                 session_cookie_samesite: str = "Lax",
                 session_expire_at_browser_close: bool = False,
                 session_save_every_request: bool = False):
        """
        Initialize the session middleware.
        
        Args:
            app: The FastAPI application
            session_store: Session storage backend
            session_cookie_name: Name of the session cookie
            session_cookie_age: Session cookie age in seconds
            session_cookie_domain: Session cookie domain
            session_cookie_secure: Whether session cookie is secure
            session_cookie_httponly: Whether session cookie is httpOnly
            session_cookie_samesite: Session cookie SameSite setting
            session_expire_at_browser_close: Whether to expire session at browser close
            session_save_every_request: Whether to save session on every request
        """
        super().__init__(app)
        
        self.session_store = session_store or MemorySessionStore()
        self.session_cookie_name = session_cookie_name
        self.session_cookie_age = session_cookie_age
        self.session_cookie_domain = session_cookie_domain
        self.session_cookie_secure = session_cookie_secure
        self.session_cookie_httponly = session_cookie_httponly
        self.session_cookie_samesite = session_cookie_samesite
        self.session_expire_at_browser_close = session_expire_at_browser_close
        self.session_save_every_request = session_save_every_request
    
    def _generate_session_key(self) -> str:
        """Generate a new session key."""
        return secrets.token_urlsafe(32)
    
    def _get_session_key(self, request: Request) -> Optional[str]:
        """Get session key from request cookies."""
        return request.cookies.get(self.session_cookie_name)
    
    def _set_session_key(self, response: Response, session_key: str) -> None:
        """Set session key in response cookies."""
        max_age = None if self.session_expire_at_browser_close else self.session_cookie_age
        
        response.set_cookie(
            self.session_cookie_name,
            session_key,
            max_age=max_age,
            domain=self.session_cookie_domain,
            secure=self.session_cookie_secure,
            httponly=self.session_cookie_httponly,
            samesite=self.session_cookie_samesite
        )
    
    def _delete_session_key(self, response: Response) -> None:
        """Delete session key from response cookies."""
        response.delete_cookie(
            self.session_cookie_name,
            domain=self.session_cookie_domain
        )
    
    def _get_session_expiry(self) -> int:
        """Get session expiry timestamp."""
        if self.session_expire_at_browser_close:
            return int(time.time()) + self.session_cookie_age
        return int(time.time()) + self.session_cookie_age
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through session middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Get session key from cookies
        session_key = self._get_session_key(request)
        
        # Initialize session data
        session_data = {}
        session_modified = False
        
        if session_key:
            # Load existing session
            session_data = self.session_store.get(session_key) or {}
        else:
            # Create new session
            session_key = self._generate_session_key()
            session_data = {}
        
        # Attach session to request
        request.state.session = session_data
        request.state.session_key = session_key
        request.state.session_modified = session_modified
        
        # Process request
        response = await call_next(request)
        
        # Handle session after request processing
        session_data = getattr(request.state, 'session', {})
        session_modified = getattr(request.state, 'session_modified', False)
        
        if session_key and (session_modified or self.session_save_every_request):
            # Save session data
            expiry = self._get_session_expiry()
            self.session_store.set(session_key, session_data, expiry)
            
            # Set session cookie
            self._set_session_key(response, session_key)
        elif session_key and not session_data:
            # Delete empty session
            self.session_store.delete(session_key)
            self._delete_session_key(response)
        elif not session_key and session_data:
            # Create new session for new data
            session_key = self._generate_session_key()
            expiry = self._get_session_expiry()
            self.session_store.set(session_key, session_data, expiry)
            self._set_session_key(response, session_key)
        
        return response


def get_session(request: Request) -> Dict[str, Any]:
    """
    Get session data from request.
    
    Args:
        request: The request object
        
    Returns:
        Session data dictionary
    """
    return getattr(request.state, 'session', {})


def set_session_data(request: Request, key: str, value: Any) -> None:
    """
    Set session data.
    
    Args:
        request: The request object
        key: Session key
        value: Session value
    """
    if not hasattr(request.state, 'session'):
        request.state.session = {}
    
    request.state.session[key] = value
    request.state.session_modified = True


def get_session_data(request: Request, key: str, default: Any = None) -> Any:
    """
    Get session data by key.
    
    Args:
        request: The request object
        key: Session key
        default: Default value if key doesn't exist
        
    Returns:
        Session value or default
    """
    session = getattr(request.state, 'session', {})
    return session.get(key, default)


def delete_session_data(request: Request, key: str) -> None:
    """
    Delete session data by key.
    
    Args:
        request: The request object
        key: Session key to delete
    """
    if hasattr(request.state, 'session') and key in request.state.session:
        del request.state.session[key]
        request.state.session_modified = True


def clear_session(request: Request) -> None:
    """
    Clear all session data.
    
    Args:
        request: The request object
    """
    if hasattr(request.state, 'session'):
        request.state.session.clear()
        request.state.session_modified = True
