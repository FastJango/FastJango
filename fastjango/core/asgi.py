"""
ASGI application configuration for FastJango.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from fastjango.core.logging import Logger
from fastjango.urls import Path as UrlPath

logger = Logger("fastjango.core.asgi")


def get_settings():
    """
    Import and return the settings module.
    
    Returns:
        The settings module
    """
    settings_module = os.environ.get("FASTJANGO_SETTINGS_MODULE")
    if not settings_module:
        raise ImportError(
            "No settings module found. Set the FASTJANGO_SETTINGS_MODULE "
            "environment variable before importing fastjango.core.asgi"
        )
    
    try:
        return importlib.import_module(settings_module)
    except ImportError as e:
        logger.error(f"Failed to import settings module: {e}", exc_info=True)
        raise ImportError(f"Failed to import settings module: {e}")


def get_asgi_application() -> FastAPI:
    """
    Create and return an ASGI application for FastJango.
    
    Returns:
        The ASGI application
    """
    # Import settings
    settings = get_settings()
    
    # Get project name from settings module
    project_name = settings.__name__.split('.')[0]
    
    # Get debug setting
    debug = getattr(settings, "DEBUG", False)
    
    # Create FastAPI app
    app = FastAPI(
        title=project_name,
        description=f"{project_name} API",
        version="1.0.0",
        debug=debug,
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "CORS_ALLOW_ORIGINS", ["*"]),
        allow_credentials=getattr(settings, "CORS_ALLOW_CREDENTIALS", True),
        allow_methods=getattr(settings, "CORS_ALLOW_METHODS", ["*"]),
        allow_headers=getattr(settings, "CORS_ALLOW_HEADERS", ["*"]),
    )
    
    # Mount static files
    static_url = getattr(settings, "STATIC_URL", "/static/")
    static_root = getattr(settings, "STATIC_ROOT", None)
    
    # Ensure static_url starts with '/'
    if static_url and not static_url.startswith('/'):
        static_url = f"/{static_url}"
    
    if static_root:
        # Create the directory if it doesn't exist
        static_dir = Path(static_root)
        if not static_dir.exists():
            try:
                logger.info(f"Creating static directory: {static_dir}")
                static_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create static directory: {e}")
        
        # Mount static files
        try:
            app.mount(static_url, StaticFiles(directory=static_root), name="static")
            logger.info(f"Mounted static files at {static_url}")
        except Exception as e:
            logger.warning(f"Failed to mount static files: {e}")
    
    # Mount media files
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_root = getattr(settings, "MEDIA_ROOT", None)
    
    # Ensure media_url starts with '/'
    if media_url and not media_url.startswith('/'):
        media_url = f"/{media_url}"
    
    if media_root:
        # Create the directory if it doesn't exist
        media_dir = Path(media_root)
        if not media_dir.exists():
            try:
                logger.info(f"Creating media directory: {media_dir}")
                media_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create media directory: {e}")
        
        # Mount media files
        try:
            app.mount(media_url, StaticFiles(directory=media_root), name="media")
            logger.info(f"Mounted media files at {media_url}")
        except Exception as e:
            logger.warning(f"Failed to mount media files: {e}")
    
    # Setup templates
    templates_dir = getattr(settings, "TEMPLATES_DIR", "templates")
    templates = Jinja2Templates(directory=templates_dir)
    
    # Flag to track if root route was registered
    root_route_registered = False
    
    # Register URLs from the urls.py file directly
    try:
        urls_module_name = f"{project_name}.urls"
        urls_module = importlib.import_module(urls_module_name)
        
        if hasattr(urls_module, "urlpatterns"):
            from fastjango.http import JsonResponse
            
            def register_urls(patterns, prefix=""):
                """Helper function to register URL patterns recursively"""
                nonlocal root_route_registered
                
                for url_pattern in patterns:
                    # Handle direct paths
                    if isinstance(url_pattern, UrlPath):
                        path_value = url_pattern.path
                        full_path = f"{prefix}/{path_value}" if path_value else prefix or "/"
                        if not full_path.startswith('/'):
                            full_path = f"/{full_path}"
                        
                        # Register the route with FastAPI
                        app.add_api_route(
                            full_path, 
                            url_pattern.view,
                            methods=["GET"],
                            name=getattr(url_pattern, "name", None)
                        )
                        logger.info(f"Registered URL pattern for {full_path}")
                        
                        # Check if this is the root route
                        if full_path == "/":
                            root_route_registered = True
                    
                    # Handle included paths
                    elif isinstance(url_pattern, tuple) and len(url_pattern) == 2:
                        # Here url_pattern is a tuple of (included_patterns, namespace)
                        included_patterns, namespace = url_pattern
                        
                        # If we have a third element which is the include path
                        # This is a special case for our include() function
                        included_path = ""
                        if len(url_pattern) > 2 and isinstance(url_pattern[2], str):
                            included_path = url_pattern[2]  # This should be the path from include
                        elif hasattr(url_pattern, "path"):
                            included_path = url_pattern.path  # Fallback for Path instances with include
                        
                        new_prefix = prefix
                        if included_path:
                            new_prefix = f"{prefix}/{included_path}" if prefix else f"/{included_path}"
                        
                        # If it's an API include, try to handle it specially
                        if "api" in included_path:
                            try:
                                api_module_path = f"{project_name}.api.urls"
                                if '.' in included_path:
                                    api_module_path = included_path
                                
                                api_module = importlib.import_module(api_module_path)
                                
                                if hasattr(api_module, "urlpatterns"):
                                    # Recursively register API patterns
                                    register_urls(api_module.urlpatterns, new_prefix)
                            except ImportError:
                                logger.warning(f"Could not import API module: {api_module_path}")
                            except Exception as e:
                                logger.warning(f"Error registering API routes: {e}")
                        else:
                            # Recursively register the included patterns
                            register_urls(included_patterns, new_prefix)
            
            # Start registering URLs from the root urlpatterns
            register_urls(urls_module.urlpatterns)
            logger.info(f"Registered URL patterns from {urls_module_name}")
    except ImportError:
        logger.warning(f"Could not import URLs module: {project_name}.urls")
    except Exception as e:
        logger.error(f"Error registering URL patterns: {e}", exc_info=True)
    
    # Include routes from apps in INSTALLED_APPS
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
    
    for app_name in installed_apps:
        try:
            # Try to import app's routes module
            routes_module = f"{app_name}.routes"
            routes = importlib.import_module(routes_module)
            
            if hasattr(routes, "router"):
                # Include router
                app.include_router(routes.router)
                logger.info(f"Included routes from {app_name}")
        except ImportError:
            # App doesn't have routes, skip
            pass
        except Exception as e:
            logger.warning(f"Failed to include routes from {app_name}: {e}")
    
    # Setup any WSGI application for compatibility
    try:
        # Try to import WSGI application
        wsgi_module = f"{project_name}.wsgi"
        wsgi = importlib.import_module(wsgi_module)
        
        if hasattr(wsgi, "application"):
            # Mount WSGI app under /django path for compatibility
            app.mount("/django", WSGIMiddleware(wsgi.application))
            logger.info(f"Mounted WSGI application at /django")
    except ImportError:
        # No WSGI application, skip
        logger.warning(f"WSGI application module '{wsgi_module}' not found, skipping")
    except Exception as e:
        logger.warning(f"Failed to mount WSGI application: {e}")
    
    # Add a default DEBUG welcome page or fallback route if no root route was registered
    if not root_route_registered:
        @app.get("/", include_in_schema=False)
        async def default_root(request: Request):
            if debug:
                # Django-like welcome page for DEBUG mode
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>{project_name} - FastJango</title>
                    <style>
                        body {{
                            background-color: #f9f9f9;
                            color: #333;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                            margin: 0;
                            padding: 0;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            text-align: center;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            padding: 2rem;
                        }}
                        h1 {{
                            font-size: 2.5rem;
                            margin-bottom: 1.5rem;
                            color: #0C4B33;
                        }}
                        .rocket {{
                            margin: 2rem 0;
                            width: 200px;
                            height: auto;
                        }}
                        .info {{
                            background-color: #e9f4fb;
                            border-radius: 8px;
                            padding: 1.5rem;
                            margin: 1.5rem 0;
                            text-align: left;
                        }}
                        .debug {{
                            color: #0C4B33;
                            font-weight: bold;
                        }}
                        .links {{
                            display: flex;
                            justify-content: center;
                            margin-top: 2rem;
                            gap: 2rem;
                        }}
                        .links a {{
                            display: flex;
                            align-items: center;
                            color: #0C4B33;
                            text-decoration: none;
                            font-weight: 500;
                        }}
                        svg {{
                            margin-right: 0.5rem;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>FastJango</h1>
                        
                        <div style="text-align:center;">
                            <svg class="rocket" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#44B78B">
                                <path d="M12,2.5c0,0,4.5,2.04,4.5,10.5c0,2.49-1.04,5.57-1.6,7H9.1c-0.56-1.43-1.6-4.51-1.6-7C7.5,4.54,12,2.5,12,2.5z"/>
                                <circle cx="12" cy="11" r="2" fill="white"/>
                                <path d="M7,20h10c0,1.1-0.9,2-2,2H9C7.9,22,7,21.1,7,20z"/>
                                <path d="M12,2.5c0,0-4.5,2.04-4.5,10.5c0,1.38,0.32,2.91,0.69,4.25c-0.77,0.46-1.69,1.25-1.69,2.25 c0,1.24,1.43,2.25,3.2,2.25c0.78,0,1.5-0.21,2.06-0.55C12.14,21.64,12.57,22,13.25,22c0.92,0,1.66-0.79,1.66-1.75 c0-0.37-0.12-0.7-0.32-0.96c0.23-0.28,0.37-0.65,0.37-1.04c0-0.66-0.39-1.25-0.98-1.63C14.46,14.96,16.5,12,16.5,8 C16.5,4.54,12,2.5,12,2.5z" fill-opacity="0.3"/>
                            </svg>
                        </div>
                        
                        <h2>The install worked successfully! Congratulations!</h2>
                        
                        <div class="info">
                            <p>You are seeing this page because <span class="debug">DEBUG=True</span> is in your settings file and you haven't configured any URLs.</p>
                        </div>
                        
                        <div class="links">
                            <a href="https://fastapi.tiangolo.com/">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0C4B33" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="16" x2="12" y2="12"></line>
                                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                                </svg>
                                FastAPI Docs
                            </a>
                            <a href="/docs">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0C4B33" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                    <line x1="16" y1="13" x2="8" y2="13"></line>
                                    <line x1="16" y1="17" x2="8" y2="17"></line>
                                    <polyline points="10 9 9 9 8 9"></polyline>
                                </svg>
                                API Docs
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
            else:
                # Just return a basic message in non-DEBUG mode
                from fastjango.http import JsonResponse
                return JsonResponse({"message": f"Welcome to {project_name}"})
    
    # Return the app
    return app 