"""
WSGI handlers for FastJango.
"""

from fastapi import FastAPI
from starlette.applications import Starlette


class WSGIHandler:
    """
    A WSGI handler for FastJango.
    
    This provides a Django-like WSGI interface over FastAPI/Starlette.
    """
    
    def __init__(self):
        """Initialize the WSGI handler."""
        self.app = FastAPI()
    
    def __call__(self, environ, start_response):
        """
        WSGI interface.
        
        Args:
            environ: WSGI environment
            start_response: WSGI start_response function
            
        Returns:
            WSGI response iterator
        """
        # Convert this to Starlette ASGI application
        starlette_app = Starlette(debug=True)
        
        # Use Starlette's internal WSGI adapter
        return starlette_app(environ, start_response) 