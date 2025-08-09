"""
Example usage of FastJango Django-like static files system.

This demonstrates how to set up and use static files with Django-like syntax
while leveraging FastAPI's performance.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

from fastjango.static import (
    StaticFiles, StaticFilesHandler, collectstatic,
    StaticFilesMiddleware, DevelopmentStaticFilesMiddleware,
    static_url, get_static_path, is_static_file,
    setup_static_files, setup_static_middleware, setup_static_utils
)


# Example 1: Basic static files setup
def example_basic_setup():
    """Example of basic static files setup."""
    app = FastAPI(title="FastJango Static Files Example")
    
    # Django-like settings
    settings = {
        'STATIC_URL': '/static/',
        'STATIC_ROOT': 'staticfiles',
        'STATICFILES_DIRS': ['static', 'app_static'],
        'DEBUG': True
    }
    
    # Set up static files
    setup_static_files(app, settings)
    
    # Set up static middleware
    setup_static_middleware(app, settings)
    
    # Set up static utilities
    setup_static_utils(app, settings)
    
    return app


# Example 2: Manual static files setup
def example_manual_setup():
    """Example of manual static files setup."""
    app = FastAPI(title="FastJango Manual Static Files")
    
    # Create static files handler
    handler = StaticFilesHandler(
        static_dirs=['static', 'app_static'],
        static_url='/static/'
    )
    
    # Mount static files
    handler.mount_all(app)
    
    # Add static file endpoints
    @app.get("/static-info/{filename:path}")
    async def get_static_info(filename: str):
        """Get information about a static file."""
        file_info = handler.find_file(filename)
        if file_info:
            return file_info
        return {"error": "File not found"}
    
    return app


# Example 3: Development vs Production setup
def example_dev_prod_setup():
    """Example showing development vs production static files setup."""
    app = FastAPI(title="FastJango Dev/Prod Static Files")
    
    # Settings based on environment
    is_development = os.getenv('ENVIRONMENT') == 'development'
    
    if is_development:
        # Development: serve from multiple directories
        settings = {
            'STATIC_URL': '/static/',
            'STATICFILES_DIRS': ['static', 'app_static', 'vendor_static'],
            'DEBUG': True
        }
        
        # Use development middleware with debug features
        middleware = DevelopmentStaticFilesMiddleware(
            app,
            static_url='/static/',
            static_dirs=['static', 'app_static', 'vendor_static'],
            debug=True
        )
    else:
        # Production: serve from collected static files
        settings = {
            'STATIC_URL': '/static/',
            'STATIC_ROOT': 'staticfiles',
            'DEBUG': False
        }
        
        # Use production middleware
        middleware = StaticFilesMiddleware(
            app,
            static_url='/static/',
            static_dirs=['staticfiles']
        )
    
    # Set up static files
    setup_static_files(app, settings)
    
    return app


# Example 4: Static file collection
def example_collect_static():
    """Example of collecting static files."""
    # Django-like collectstatic command
    source_dirs = ['static', 'app_static', 'vendor_static']
    destination = 'staticfiles'
    
    # Collect static files
    result = collectstatic(
        source_dirs=source_dirs,
        destination=destination,
        ignore_patterns=['*.pyc', '__pycache__', '.git'],
        dry_run=False
    )
    
    print(f"Collected {result['total_collected']} files")
    print(f"Skipped {result['total_skipped']} files")
    
    return result


# Example 5: Template integration
def example_template_integration():
    """Example of static files in templates."""
    app = FastAPI(title="FastJango Template Static Files")
    
    # Set up static files
    settings = {
        'STATIC_URL': '/static/',
        'STATICFILES_DIRS': ['static'],
        'DEBUG': True
    }
    
    setup_static_files(app, settings)
    setup_static_utils(app, settings)
    
    @app.get("/", response_class=HTMLResponse)
    async def home_page(request: Request):
        """Home page with static files in template."""
        # Get static URL helpers
        static_url = request.app.state.static_url
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FastJango Static Files Example</title>
            <link rel="stylesheet" href="{static_url}/css/style.css">
            <script src="{static_url}/js/app.js"></script>
        </head>
        <body>
            <h1>FastJango Static Files Example</h1>
            <p>This page uses static files with Django-like syntax.</p>
            <img src="{static_url}/images/logo.png" alt="Logo">
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    return app


# Example 6: Advanced static file features
def example_advanced_features():
    """Example of advanced static file features."""
    app = FastAPI(title="FastJango Advanced Static Files")
    
    # Set up static files with advanced features
    settings = {
        'STATIC_URL': '/static/',
        'STATICFILES_DIRS': ['static'],
        'DEBUG': True
    }
    
    setup_static_files(app, settings)
    setup_static_utils(app, settings)
    
    @app.get("/static-hash/{filename:path}")
    async def get_static_hash(filename: str):
        """Get static file with hash for cache busting."""
        from fastjango.static.utils import get_static_hash, static_url_with_hash
        
        file_hash = get_static_hash(filename, settings['STATICFILES_DIRS'])
        url_with_hash = static_url_with_hash(filename, settings['STATIC_URL'], settings['STATICFILES_DIRS'])
        
        return {
            'filename': filename,
            'hash': file_hash,
            'url': static_url(filename, settings['STATIC_URL']),
            'url_with_hash': url_with_hash
        }
    
    @app.get("/static-manifest/")
    async def get_static_manifest():
        """Get static file manifest."""
        from fastjango.static.utils import get_static_manifest
        
        return get_static_manifest(settings['STATICFILES_DIRS'])
    
    @app.get("/static-files/")
    async def list_static_files():
        """List all static files."""
        from fastjango.static.utils import find_static_files
        
        files = {}
        for static_dir in settings['STATICFILES_DIRS']:
            files[static_dir] = find_static_files(static_dir)
        
        return files
    
    return app


# Example 7: Custom static file serving
def example_custom_serving():
    """Example of custom static file serving."""
    app = FastAPI(title="FastJango Custom Static Files")
    
    @app.get("/custom-static/{filename:path}")
    async def serve_custom_static(filename: str):
        """Serve static files with custom logic."""
        from fastjango.static.utils import get_static_path, get_static_file_info
        from fastjango.static.files import serve_static_file
        
        # Check if file exists
        file_path = get_static_path(filename, ['static'])
        if not file_path:
            return {"error": "File not found"}
        
        # Get file info
        file_info = get_static_file_info(filename, ['static'])
        
        # Custom logic: only serve certain file types
        allowed_types = ['.css', '.js', '.png', '.jpg', '.gif']
        if not any(filename.endswith(ext) for ext in allowed_types):
            return {"error": "File type not allowed"}
        
        # Serve the file
        return serve_static_file(str(file_path))
    
    return app


# Example 8: Static file middleware with custom logic
def example_custom_middleware():
    """Example of custom static file middleware."""
    from fastjango.static.middleware import StaticFilesMiddleware
    
    class CustomStaticFilesMiddleware(StaticFilesMiddleware):
        """Custom static files middleware with additional features."""
        
        def __init__(self, app, **kwargs):
            super().__init__(app, **kwargs)
            self.allowed_extensions = ['.css', '.js', '.png', '.jpg', '.gif', '.ico']
        
        async def _serve_static_file(self, request):
            """Serve static file with custom logic."""
            url_path = request.url.path
            file_path = url_path[len(self.static_url):].lstrip('/')
            
            # Check file extension
            if not any(file_path.endswith(ext) for ext in self.allowed_extensions):
                raise HTTPException(status_code=403, detail="File type not allowed")
            
            # Continue with normal serving
            return await super()._serve_static_file(request)
    
    app = FastAPI(title="FastJango Custom Static Middleware")
    
    # Use custom middleware
    middleware = CustomStaticFilesMiddleware(
        app,
        static_url='/static/',
        static_dirs=['static']
    )
    
    return app


# Example 9: Static file compression
def example_static_compression():
    """Example of static file compression."""
    app = FastAPI(title="FastJango Static Compression")
    
    @app.get("/compressed-static/{filename:path}")
    async def serve_compressed_static(filename: str):
        """Serve compressed static files."""
        from fastjango.static.utils import get_static_path
        import gzip
        import mimetypes
        
        file_path = get_static_path(filename, ['static'])
        if not file_path:
            return {"error": "File not found"}
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Compress content
        compressed_content = gzip.compress(content)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or 'application/octet-stream'
        
        # Return compressed response
        from fastapi.responses import Response
        return Response(
            content=compressed_content,
            media_type=content_type,
            headers={
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(compressed_content))
            }
        )
    
    return app


# Example 10: Complete static files setup
def example_complete_setup():
    """Complete example of static files setup."""
    app = FastAPI(title="FastJango Complete Static Files")
    
    # Django-like settings
    settings = {
        'STATIC_URL': '/static/',
        'STATIC_ROOT': 'staticfiles',
        'STATICFILES_DIRS': ['static', 'app_static'],
        'DEBUG': True,
        'STATICFILES_FINDERS': [
            'fastjango.static.finders.FileSystemFinder',
            'fastjango.static.finders.AppDirectoriesFinder',
        ],
        'STATICFILES_STORAGE': 'fastjango.static.storage.StaticFilesStorage',
    }
    
    # Set up static files
    setup_static_files(app, settings)
    setup_static_middleware(app, settings)
    setup_static_utils(app, settings)
    
    # Add static file management endpoints
    @app.post("/collect-static/")
    async def collect_static_endpoint():
        """Collect static files endpoint."""
        result = collectstatic(
            source_dirs=settings['STATICFILES_DIRS'],
            destination=settings['STATIC_ROOT'],
            ignore_patterns=['*.pyc', '__pycache__', '.git']
        )
        return result
    
    @app.get("/static-status/")
    async def static_status():
        """Get static files status."""
        from fastjango.static.utils import get_static_manifest
        
        return {
            'static_url': settings['STATIC_URL'],
            'static_root': settings['STATIC_ROOT'],
            'staticfiles_dirs': settings['STATICFILES_DIRS'],
            'manifest': get_static_manifest(settings['STATICFILES_DIRS'])
        }
    
    return app


if __name__ == "__main__":
    # Run examples
    print("FastJango Static Files Examples")
    print("=" * 50)
    
    # Example 1: Basic setup
    app1 = example_basic_setup()
    print("✅ Basic static files setup")
    
    # Example 2: Manual setup
    app2 = example_manual_setup()
    print("✅ Manual static files setup")
    
    # Example 3: Dev/Prod setup
    app3 = example_dev_prod_setup()
    print("✅ Development/Production setup")
    
    # Example 4: Collect static
    result = example_collect_static()
    print("✅ Static file collection")
    
    # Example 5: Template integration
    app5 = example_template_integration()
    print("✅ Template integration")
    
    # Example 6: Advanced features
    app6 = example_advanced_features()
    print("✅ Advanced features")
    
    # Example 7: Custom serving
    app7 = example_custom_serving()
    print("✅ Custom serving")
    
    # Example 8: Custom middleware
    app8 = example_custom_middleware()
    print("✅ Custom middleware")
    
    # Example 9: Compression
    app9 = example_static_compression()
    print("✅ Static compression")
    
    # Example 10: Complete setup
    app10 = example_complete_setup()
    print("✅ Complete setup")
    
    print("\n🎉 All static files examples completed!")
    print("\nFeatures demonstrated:")
    print("- Django-like static file serving")
    print("- Multiple static directories")
    print("- Development vs production setup")
    print("- Static file collection")
    print("- Template integration")
    print("- Cache busting with hashes")
    print("- Custom middleware")
    print("- File compression")
    print("- Static file manifests")
