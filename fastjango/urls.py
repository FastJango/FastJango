"""
URL routing utilities for FastJango.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.routing import APIRoute

from fastjango.core.dependencies import get_current_user
from fastjango.http import HttpResponse


class Path:
    """
    A path definition for URL routing.
    """
    
    def __init__(self, path: str, view: Callable, name: Optional[str] = None):
        """
        Initialize a path.
        
        Args:
            path: The URL path
            view: The view function or class
            name: The name of the path
        """
        self.path = path
        self.view = view
        self.name = name


def path(path: str, view: Callable, name: Optional[str] = None) -> Path:
    """
    Define a path for URL routing.
    
    Args:
        path: The URL path
        view: The view function or class
        name: The name of the path
        
    Returns:
        A Path object
    """
    return Path(path, view, name)


class Include:
    """
    A class to store included URL patterns.
    """
    
    def __init__(self, patterns: List[Path], namespace: Optional[str], path: str):
        """
        Initialize an include.
        
        Args:
            patterns: The URL patterns to include
            namespace: The namespace for the included patterns
            path: The path prefix for the included patterns
        """
        self.patterns = patterns
        self.namespace = namespace
        self.path = path


def include(module_path: str, namespace: Optional[str] = None) -> Tuple[List[Path], Optional[str], str]:
    """
    Include paths from another module.
    
    Args:
        module_path: The module path to include
        namespace: Optional namespace override
        
    Returns:
        A tuple of (paths, namespace, module_path)
    """
    # Import the module
    import importlib
    
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import '{module_path}'. {e}")
    
    # Get the urlpatterns from the module
    urlpatterns = getattr(module, "urlpatterns", [])
    
    # Get the app_name from the module or use the provided namespace
    app_name = namespace or getattr(module, "app_name", None)
    
    # Extract the path from the module path (last part)
    path_part = module_path.split(".")[-1]
    
    # Return an Include object
    return urlpatterns, app_name, path_part


class URLResolver:
    """
    A URL resolver for FastJango.
    """
    
    def __init__(self, urlpatterns: List[Path], router: Optional[APIRouter] = None):
        """
        Initialize a URL resolver.
        
        Args:
            urlpatterns: The URL patterns to resolve
            router: The FastAPI router to use
        """
        self.urlpatterns = urlpatterns
        self.router = router or APIRouter()
        
        # Register all URL patterns
        self._register_patterns(urlpatterns)
    
    def _register_patterns(self, patterns: List[Path], prefix: str = "") -> None:
        """
        Register URL patterns with the router.
        
        Args:
            patterns: The URL patterns to register
            prefix: The URL prefix to use
        """
        for pattern in patterns:
            if isinstance(pattern, Path):
                # Add the path to the router
                self._add_path(pattern, prefix)
            elif isinstance(pattern, tuple) and len(pattern) >= 2:
                # Handle included urlpatterns
                included_patterns, namespace = pattern[0], pattern[1]
                
                # Get the path from the tuple if it exists (returned by include())
                path_prefix = ""
                if len(pattern) > 2 and pattern[2]:
                    path_prefix = pattern[2]
                
                # Build the new prefix
                included_prefix = f"{prefix}/{path_prefix}" if prefix else path_prefix
                
                # Register the included patterns
                self._register_patterns(included_patterns, included_prefix)
    
    def _add_path(self, path: Path, prefix: str = "") -> None:
        """
        Add a path to the router.
        
        Args:
            path: The path to add
            prefix: The URL prefix to use
        """
        # Combine prefix and path
        full_path = prefix
        if path.path:
            if full_path and not full_path.endswith('/'):
                full_path += '/'
            full_path += path.path
        
        # Convert Django-style path to FastAPI path
        fastapi_path = self._convert_path(full_path)
        
        # Register the route with FastAPI
        self.router.add_api_route(
            fastapi_path,
            path.view,
            methods=["GET"],
            name=path.name,
            response_class=HttpResponse,
        )
    
    def _convert_path(self, path: str) -> str:
        """
        Convert a Django-style path to a FastAPI path.
        
        Args:
            path: The Django-style path
            
        Returns:
            The FastAPI-style path
        """
        # Replace Django-style path parameters with FastAPI-style
        # e.g., /<int:id>/ becomes /{id}/
        path = re.sub(r'<int:(\w+)>', r'{\1}', path)
        path = re.sub(r'<str:(\w+)>', r'{\1}', path)
        path = re.sub(r'<slug:(\w+)>', r'{\1}', path)
        path = re.sub(r'<uuid:(\w+)>', r'{\1}', path)
        path = re.sub(r'<path:(\w+)>', r'{\1}', path)
        
        # Remove trailing slash if present
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        
        # Ensure path starts with a slash for FastAPI
        if path and not path.startswith('/'):
            path = '/' + path
        
        return path 