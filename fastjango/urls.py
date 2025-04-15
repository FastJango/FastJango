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
        # Ensure path doesn't start with a slash for consistency
        self.path = path[1:] if path.startswith('/') else path
        self.view = view
        self.name = name
        self.methods = ["GET"]  # Default to GET method
        self.kwargs = {}  # Additional kwargs for add_api_route


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
    
    # Extract the path prefix - use the last component of the module path 
    # that isn't 'urls' (which is a convention, not part of the URL)
    path_parts = module_path.split(".")
    path_prefix = ""
    
    for part in reversed(path_parts):
        if part != "urls":
            path_prefix = part
            break
    
    # Ensure path_prefix doesn't start with a slash
    if path_prefix.startswith('/'):
        path_prefix = path_prefix[1:]
    
    # Return a tuple with the urlpatterns, app_name and path_prefix
    return urlpatterns, app_name, path_prefix


class URLResolver:
    """
    A URL resolver for FastJango.
    """
    
    def __init__(self, router: APIRouter) -> None:
        """
        Initialize the URL resolver.
        
        Args:
            router: The FastAPI router to use
        """
        self.router = router

    def register(self, urlpatterns: List[Path], prefix: str = "") -> None:
        """
        Register URL patterns with the FastAPI router.
        
        Args:
            urlpatterns: The URL patterns to register
            prefix: The URL prefix to use
        """
        for path_obj in urlpatterns:
            if isinstance(path_obj.view, tuple):
                # This is a result of include()
                included_patterns, namespace, included_prefix = path_obj.view
                
                # Combine the prefixes properly
                combined_prefix = prefix
                if path_obj.path:
                    # Ensure path doesn't start with a slash when adding to prefix
                    route = path_obj.path
                    if route.startswith('/'):
                        route = route[1:]
                    
                    # Handle case where prefix is empty
                    if combined_prefix:
                        combined_prefix = f"{combined_prefix}/{route}"
                    else:
                        combined_prefix = route
                
                # Register included patterns with the combined prefix
                self.register(included_patterns, prefix=combined_prefix)
            else:
                # Convert the path to FastAPI format
                route_path = self._convert_path(path_obj.path)
                
                # Add prefix if present
                if prefix:
                    # Format prefix properly
                    clean_prefix = prefix
                    if clean_prefix.startswith('/'):
                        clean_prefix = clean_prefix[1:]
                    if clean_prefix.endswith('/'):
                        clean_prefix = clean_prefix[:-1]
                    
                    if route_path == "/":
                        route_path = f"/{clean_prefix}"
                    else:
                        route_path = f"/{clean_prefix}{route_path}"
                
                # Register the route with the FastAPI router
                try:
                    self.router.add_api_route(
                        route_path,
                        path_obj.view,
                        name=path_obj.name,
                    )
                except Exception as e:
                    from fastjango.core.logging import Logger
                    logger = Logger("fastjango.urls")
                    logger.error(f"Failed to register route {route_path}: {e}")
    
    def _convert_path(self, path: str) -> str:
        """
        Convert a Django-style path to a FastAPI path.
        
        Args:
            path: The Django-style path
            
        Returns:
            The FastAPI-style path
        """
        # Normalize multiple slashes to single slashes
        path = re.sub(r'//+', '/', path)
        
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
        if not path.startswith('/'):
            path = '/' + path
        elif path == "":
            path = "/"
        
        return path 