"""
FastJango CSRF Protection - Django-like CSRF protection for FastJango.
"""

import secrets
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFProtection:
    """
    CSRF protection class that mimics Django's CSRF protection.
    """
    
    def __init__(self, secret_key: str = None, cookie_name: str = 'csrftoken', 
                 header_name: str = 'X-CSRFToken', timeout: int = 3600):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for token generation
            cookie_name: Name of the CSRF cookie
            header_name: Name of the CSRF header
            timeout: Token timeout in seconds
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.timeout = timeout
    
    def get_token(self, request: Request) -> str:
        """
        Get or generate a CSRF token.
        
        Args:
            request: The request object
            
        Returns:
            The CSRF token
        """
        # Check if token exists in cookies
        token = request.cookies.get(self.cookie_name)
        
        if not token or not self._validate_token(token):
            # Generate new token
            token = self._generate_token()
        
        return token
    
    def _generate_token(self) -> str:
        """
        Generate a new CSRF token.
        
        Returns:
            The generated token
        """
        timestamp = str(int(time.time()))
        message = f"{timestamp}:{self.secret_key}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{signature}"
    
    def _validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parts = token.split(':')
            if len(parts) != 2:
                return False
            
            timestamp, signature = parts
            timestamp = int(timestamp)
            
            # Check if token is expired
            if time.time() - timestamp > self.timeout:
                return False
            
            # Verify signature
            message = f"{timestamp}:{self.secret_key}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, TypeError):
            return False
    
    def validate_token(self, request: Request) -> bool:
        """
        Validate the CSRF token from the request.
        
        Args:
            request: The request object
            
        Returns:
            True if valid, False otherwise
        """
        # Skip validation for safe methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Get token from header or form data
        token = request.headers.get(self.header_name)
        if not token:
            # Try to get from form data
            form_data = request.form()
            token = form_data.get('csrfmiddlewaretoken')
        
        if not token:
            return False
        
        return self._validate_token(token)
    
    def add_token_to_response(self, response: Response, token: str) -> Response:
        """
        Add CSRF token to response cookies.
        
        Args:
            response: The response object
            token: The CSRF token
            
        Returns:
            The response with CSRF cookie
        """
        response.set_cookie(
            self.cookie_name,
            token,
            max_age=self.timeout,
            httponly=False,  # Allow JavaScript access
            samesite='lax'
        )
        return response


# Global CSRF protection instance
_csrf_protection = CSRFProtection()


def csrf_token(request: Request) -> str:
    """
    Get the CSRF token for a request.
    
    Args:
        request: The request object
        
    Returns:
        The CSRF token
    """
    return _csrf_protection.get_token(request)


def csrf_protect(request: Request) -> bool:
    """
    Validate CSRF protection for a request.
    
    Args:
        request: The request object
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If CSRF validation fails
    """
    if not _csrf_protection.validate_token(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )
    return True


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic CSRF protection.
    """
    
    def __init__(self, app, csrf_protection: CSRFProtection = None):
        """
        Initialize the CSRF middleware.
        
        Args:
            app: The FastAPI app
            csrf_protection: CSRF protection instance
        """
        super().__init__(app)
        self.csrf_protection = csrf_protection or _csrf_protection
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request with CSRF protection.
        
        Args:
            request: The request object
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Add CSRF token to request state
        request.state.csrf_token = self.csrf_protection.get_token(request)
        
        # Validate CSRF for unsafe methods
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            if not self.csrf_protection.validate_token(request):
                return HTMLResponse(
                    content="<h1>403 Forbidden</h1><p>CSRF token validation failed.</p>",
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        # Process the request
        response = await call_next(request)
        
        # Add CSRF token to response cookies
        if hasattr(request.state, 'csrf_token'):
            self.csrf_protection.add_token_to_response(response, request.state.csrf_token)
        
        return response


# Template helpers
def csrf_token_input(token: str) -> str:
    """
    Generate a hidden input field for CSRF token.
    
    Args:
        token: The CSRF token
        
    Returns:
        HTML input field
    """
    return f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">'


def csrf_token_meta(token: str) -> str:
    """
    Generate a meta tag for CSRF token.
    
    Args:
        token: The CSRF token
        
    Returns:
        HTML meta tag
    """
    return f'<meta name="csrf-token" content="{token}">'


# JavaScript helper
CSRF_JS = """
<script>
// CSRF token handling for AJAX requests
function getCSRFToken() {
    // Try to get from meta tag
    let token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (!token) {
        // Try to get from cookie
        token = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1];
    }
    return token;
}

// Add CSRF token to all AJAX requests
document.addEventListener('DOMContentLoaded', function() {
    const token = getCSRFToken();
    if (token) {
        // Override fetch to include CSRF token
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = token;
            return originalFetch(url, options);
        };
        
        // Override XMLHttpRequest to include CSRF token
        const originalXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
            originalXHROpen.call(this, method, url, async, user, password);
            this.setRequestHeader('X-CSRFToken', token);
        };
    }
});
</script>
"""


# Example usage:
def setup_csrf_protection(app):
    """
    Set up CSRF protection for a FastAPI app.
    
    Args:
        app: The FastAPI app
    """
    # Add CSRF middleware
    app.add_middleware(CSRFMiddleware)
    
    # Add CSRF token endpoint
    @app.get("/csrf-token/")
    async def get_csrf_token(request: Request):
        """Get CSRF token for AJAX requests."""
        return {"csrf_token": csrf_token(request)}
    
    # Add CSRF error handler
    @app.exception_handler(HTTPException)
    async def csrf_exception_handler(request: Request, exc: HTTPException):
        """Handle CSRF validation errors."""
        if exc.status_code == 403 and "CSRF" in str(exc.detail):
            return HTMLResponse(
                content="""
                <h1>403 Forbidden</h1>
                <p>CSRF token validation failed. Please refresh the page and try again.</p>
                <script>setTimeout(() => window.location.reload(), 3000);</script>
                """,
                status_code=403
            )
        return exc
