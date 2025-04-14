"""
HTTP utilities for FastJango.
"""

import json
from typing import Any, Dict, List, Optional, Union

from fastapi import Response
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder


class JsonResponse(JSONResponse):
    """
    A response that renders its content as JSON.
    """
    
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background=None,
    ):
        """
        Initialize the JSON response.
        
        Args:
            content: The content to render
            status_code: The HTTP status code
            headers: HTTP headers
            media_type: The media type
            background: Background task
        """
        # Ensure content is JSON serializable
        content = jsonable_encoder(content)
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


class HttpResponse(Response):
    """
    A basic HTTP response.
    """
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background=None,
    ):
        """
        Initialize the HTTP response.
        
        Args:
            content: The content to render
            status_code: The HTTP status code
            headers: HTTP headers
            media_type: The media type
            background: Background task
        """
        if isinstance(content, str):
            pass
        elif content is not None:
            content = str(content)
        else:
            content = ""
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type or "text/html",
            background=background,
        )


class TemplateResponse(HTMLResponse):
    """
    A response that renders a template.
    """
    
    def __init__(
        self,
        request: Any,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background=None,
    ):
        """
        Initialize the template response.
        
        Args:
            request: The request
            template_name: The name of the template to render
            context: The context to render the template with
            status_code: The HTTP status code
            headers: HTTP headers
            media_type: The media type
            background: Background task
        """
        from fastjango.template import render_to_string
        
        # Render template to string
        content = render_to_string(template_name, context or {}, request)
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


def redirect(url: str, permanent: bool = False) -> RedirectResponse:
    """
    Return a redirect response.
    
    Args:
        url: The URL to redirect to
        permanent: Whether the redirect is permanent
        
    Returns:
        A redirect response
    """
    status_code = 301 if permanent else 302
    return RedirectResponse(url=url, status_code=status_code) 