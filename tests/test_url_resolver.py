#!/usr/bin/env python
"""
Test script for FastJango URL routing.
"""

import os
import sys
import shutil
import unittest
from fastapi import FastAPI, APIRouter

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# List of test fixtures to clean up
TEST_FIXTURES = [
    os.path.join(os.path.dirname(__file__), "test_app"),
    os.path.join(os.path.dirname(__file__), "nested_app"),
    os.path.join(os.path.dirname(__file__), "edge_cases"),
    os.path.join(os.path.dirname(__file__), "test_urls.py"),
    os.path.join(os.path.dirname(__file__), "test_settings.py")
]

def setup_test_fixtures():
    """Set up test fixtures needed for URL resolver testing."""
    # Setup FastJango environment
    os.environ["FASTJANGO_SETTINGS_MODULE"] = "tests.test_settings"

    # Create test settings
    test_settings_path = os.path.join(os.path.dirname(__file__), "test_settings.py")
    with open(test_settings_path, "w") as f:
        f.write("""
ROOT_URLCONF = "tests.test_urls"
DEBUG = True
INSTALLED_APPS = ["tests.test_app", "tests.nested_app", "tests.edge_cases"]
""")

    # Create test directories
    test_app_dir = os.path.join(os.path.dirname(__file__), "test_app")
    os.makedirs(test_app_dir, exist_ok=True)

    # Create test app's urls.py
    with open(os.path.join(test_app_dir, "urls.py"), "w") as f:
        f.write("""
from fastjango.urls import path, include
from fastjango.http import JsonResponse

def app_view(request):
    return JsonResponse({"message": "App view"})

def param_view(request, id):
    return JsonResponse({"id": id})

urlpatterns = [
    path("/", app_view, name="app-root"),
    path("/item/<int:id>", param_view, name="app-item"),
    path("/api", include("tests.test_app.api.urls")),
]

app_name = "test_app"
""")

    # Create test app's __init__.py
    with open(os.path.join(test_app_dir, "__init__.py"), "w") as f:
        f.write("")

    # Create test app's api directory
    api_dir = os.path.join(test_app_dir, "api")
    os.makedirs(api_dir, exist_ok=True)

    # Create test app's api/__init__.py
    with open(os.path.join(api_dir, "__init__.py"), "w") as f:
        f.write("")

    # Create test app's api/urls.py
    with open(os.path.join(api_dir, "urls.py"), "w") as f:
        f.write("""
from fastjango.urls import path, include
from fastjango.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "API root"})

def api_detail(request, item_id):
    return JsonResponse({"item_id": item_id})

urlpatterns = [
    path("/", api_root, name="api-root"),
    path("/<int:item_id>", api_detail, name="api-detail"),
    path("/v1", include("tests.test_app.api.v1.urls")),
]
""")

    # Create v1 API directory and files
    v1_dir = os.path.join(api_dir, "v1")
    os.makedirs(v1_dir, exist_ok=True)

    with open(os.path.join(v1_dir, "__init__.py"), "w") as f:
        f.write("")

    with open(os.path.join(v1_dir, "urls.py"), "w") as f:
        f.write("""
from fastjango.urls import path
from fastjango.http import JsonResponse

def v1_root(request):
    return JsonResponse({"message": "API v1"})

def v1_detail(request, id):
    return JsonResponse({"id": id, "version": "v1"})

urlpatterns = [
    path("/", v1_root, name="api-v1-root"),
    path("/<int:id>", v1_detail, name="api-v1-detail"),
]
""")

    # Create nested app
    nested_app_dir = os.path.join(os.path.dirname(__file__), "nested_app")
    os.makedirs(nested_app_dir, exist_ok=True)

    # Create nested app's __init__.py
    with open(os.path.join(nested_app_dir, "__init__.py"), "w") as f:
        f.write("")

    # Create nested app's urls.py
    with open(os.path.join(nested_app_dir, "urls.py"), "w") as f:
        f.write("""
from fastjango.urls import path
from fastjango.http import JsonResponse

def nested_view(request):
    return JsonResponse({"message": "Nested view"})

urlpatterns = [
    path("/", nested_view, name="nested-root"),
]

app_name = "nested"
""")

    # Create edge cases app
    edge_cases_dir = os.path.join(os.path.dirname(__file__), "edge_cases")
    os.makedirs(edge_cases_dir, exist_ok=True)

    with open(os.path.join(edge_cases_dir, "__init__.py"), "w") as f:
        f.write("")

    with open(os.path.join(edge_cases_dir, "urls.py"), "w") as f:
        f.write("""
from fastjango.urls import path
from fastjango.http import JsonResponse

def empty_path(request):
    return JsonResponse({"message": "Empty path"})

def trailing_slash(request):
    return JsonResponse({"message": "Trailing slash"})

def multiple_params(request, user_id, post_id):
    return JsonResponse({"user_id": user_id, "post_id": post_id})
    
def multiple_slashes(request):
    return JsonResponse({"message": "Multiple slashes"})

urlpatterns = [
    path("", empty_path, name="empty-path"),
    path("/trailing/", trailing_slash, name="trailing-slash"),
    path("/users/<int:user_id>/posts/<int:post_id>", multiple_params, name="multiple-params"),
    path("////multiple////slashes", multiple_slashes, name="multiple-slashes"),
]

app_name = "edge"
""")

    # Create test project urls.py
    test_urls_path = os.path.join(os.path.dirname(__file__), "test_urls.py")
    with open(test_urls_path, "w") as f:
        f.write("""
from fastjango.urls import path, include
from fastjango.http import JsonResponse

def index(request):
    return JsonResponse({"message": "Root view"})

def about(request):
    return JsonResponse({"message": "About view"})

urlpatterns = [
    path("/", index, name="index"),
    path("/about", about, name="about"),
    path("/app", include("tests.test_app.urls")),
    path("/nested", include("tests.nested_app.urls")),
    path("/edge", include("tests.edge_cases.urls")),
]
""")

    # Add __init__.py to tests directory
    tests_init_path = os.path.join(os.path.dirname(__file__), "__init__.py")
    if not os.path.exists(tests_init_path):
        with open(tests_init_path, "w") as f:
            f.write("")

def cleanup_test_fixtures():
    """Clean up test fixtures after tests have completed."""
    print("\nCleaning up test fixtures...")
    for fixture in TEST_FIXTURES:
        try:
            if os.path.isdir(fixture):
                shutil.rmtree(fixture)
                print(f"Removed directory: {os.path.basename(fixture)}")
            elif os.path.exists(fixture):
                os.remove(fixture)
                print(f"Removed file: {os.path.basename(fixture)}")
        except Exception as e:
            print(f"Error removing {fixture}: {e}")

# Import FastJango URL resolver
from fastjango.urls import URLResolver

def test_url_resolver():
    """Test the URL resolver."""
    print("Testing URL resolver...")
    
    # Import the URL patterns
    import importlib
    urls_module = importlib.import_module("tests.test_urls")
    urlpatterns = getattr(urls_module, "urlpatterns", [])
    
    # Create a router and resolver
    router = APIRouter()
    resolver = URLResolver(router)
    
    # Register the URL patterns
    resolver.register(urlpatterns)
    
    # Print registered routes
    print("\nRegistered routes:")
    for route in router.routes:
        print(f"Path: {route.path}, Name: {route.name}")

# Import and run FastJango ASGI app
def test_asgi_app():
    """Test the ASGI application."""
    print("\nTesting ASGI application...")
    
    # Import the ASGI application
    from fastjango.core.asgi import get_asgi_application
    
    # Create the ASGI application
    app = get_asgi_application()
    
    # Print registered routes from the FastAPI app
    print("\nRegistered ASGI routes:")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path}, Name: {route.name}")

class TestURLResolver(unittest.TestCase):
    """Test case for URL resolver."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        setup_test_fixtures()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures after all tests have completed."""
        cleanup_test_fixtures()
    
    def test_resolver(self):
        """Test URL resolver functionality."""
        # Import the URL patterns
        import importlib
        urls_module = importlib.import_module("tests.test_urls")
        urlpatterns = getattr(urls_module, "urlpatterns", [])
        
        # Create a router and resolver
        router = APIRouter()
        resolver = URLResolver(router)
        
        # Register the URL patterns
        resolver.register(urlpatterns)
        
        # Check that routes are registered
        self.assertTrue(len(router.routes) > 0)
        
        # Check specific routes
        path_names = [route.name for route in router.routes if hasattr(route, 'name')]
        self.assertIn("index", path_names)
        self.assertIn("about", path_names)

if __name__ == "__main__":
    try:
        # For manual testing, setup fixtures and run tests directly
        setup_test_fixtures()
        test_url_resolver()
        #test_asgi_app()  # Uncomment to test ASGI app
    finally:
        # Always clean up, even if tests fail
        cleanup_test_fixtures() 