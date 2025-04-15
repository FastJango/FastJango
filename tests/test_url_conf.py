#!/usr/bin/env python
"""
Tests for FastJango URL configuration functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango URL components
from fastjango.urls import (
    path,
    include,
    Path,
    URLResolver,
)
from fastjango.http import JsonResponse
from fastapi import APIRouter


# Define some test views
def index_view(request):
    return JsonResponse({"message": "Index"})

def detail_view(request, id):
    return JsonResponse({"id": id})

def another_view(request):
    return JsonResponse({"message": "Another"})


class URLPatternTest(unittest.TestCase):
    """Test suite for URL pattern creation."""
    
    def test_path_function(self):
        """Test the path function."""
        # Create a path
        url_path = path("/test", index_view, name="test")
        
        # Check that the path has the correct attributes
        self.assertIsInstance(url_path, Path)
        self.assertEqual(url_path.path, "test")  # Leading slash should be removed
        self.assertEqual(url_path.view, index_view)
        self.assertEqual(url_path.name, "test")
    
    def test_path_with_parameters(self):
        """Test path with parameters."""
        # Create a path with parameters
        url_path = path("/items/<int:id>", detail_view, name="item-detail")
        
        # Check that the path has the correct attributes
        self.assertEqual(url_path.path, "items/<int:id>")
        self.assertEqual(url_path.view, detail_view)
        self.assertEqual(url_path.name, "item-detail")


class IncludeTest(unittest.TestCase):
    """Test suite for include function."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test module with urlpatterns
        self.module_name = "test_urls_module"
        self.module = type(sys)(self.module_name)
        sys.modules[self.module_name] = self.module
        
        # Define urlpatterns in the module
        self.module.urlpatterns = [
            path("/", index_view, name="index"),
            path("/items/<int:id>", detail_view, name="item-detail"),
        ]
        
        # Add app_name to the module
        self.module.app_name = "test_app"
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test module
        del sys.modules[self.module_name]
    
    def test_include_function(self):
        """Test the include function."""
        # Include the test module
        included = include(self.module_name)
        
        # Check that include returns the correct tuple
        self.assertIsInstance(included, tuple)
        self.assertEqual(len(included), 3)
        
        # Check the components of the tuple
        patterns, namespace, prefix = included
        
        # Check patterns
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].name, "index")
        self.assertEqual(patterns[1].name, "item-detail")
        
        # Check namespace
        self.assertEqual(namespace, "test_app")
        
        # Check prefix
        self.assertEqual(prefix, "test_urls_module")
    
    def test_include_with_namespace(self):
        """Test include with custom namespace."""
        # Include the test module with a custom namespace
        included = include(self.module_name, namespace="custom")
        
        # Check that namespace is overridden
        patterns, namespace, prefix = included
        self.assertEqual(namespace, "custom")


class URLResolverTest(unittest.TestCase):
    """Test suite for URLResolver."""
    
    def test_register_patterns(self):
        """Test registering URL patterns."""
        # Create URL patterns
        urlpatterns = [
            path("/", index_view, name="index"),
            path("/items/<int:id>", detail_view, name="item-detail"),
            path("/another", another_view, name="another"),
        ]
        
        # Create a router and resolver
        router = APIRouter()
        resolver = URLResolver(router)
        
        # Register the patterns
        resolver.register(urlpatterns)
        
        # Check that the patterns were registered
        self.assertEqual(len(router.routes), 3)
        
        # Check the paths
        route_paths = [route.path for route in router.routes]
        self.assertIn("/", route_paths)
        self.assertIn("/items/{id}", route_paths)  # Parameters should be converted
        self.assertIn("/another", route_paths)
        
        # Check the names
        route_names = [getattr(route, "name", None) for route in router.routes]
        self.assertIn("index", route_names)
        self.assertIn("item-detail", route_names)
        self.assertIn("another", route_names)
    
    def test_register_included_patterns(self):
        """Test registering patterns with includes."""
        # Create a test module with urlpatterns
        module_name = "test_included_urls"
        module = type(sys)(module_name)
        sys.modules[module_name] = module
        
        # Define urlpatterns in the module
        module.urlpatterns = [
            path("/included", index_view, name="included-index"),
            path("/included/<int:id>", detail_view, name="included-detail"),
        ]
        
        # Create URL patterns with include
        urlpatterns = [
            path("/", index_view, name="index"),
            path("/sub", include(module_name)),
        ]
        
        # Create a router and resolver
        router = APIRouter()
        resolver = URLResolver(router)
        
        # Register the patterns
        resolver.register(urlpatterns)
        
        # Check that all patterns were registered
        self.assertEqual(len(router.routes), 3)
        
        # Check the paths
        route_paths = [route.path for route in router.routes]
        self.assertIn("/", route_paths)
        self.assertIn("/sub/included", route_paths)
        self.assertIn("/sub/included/{id}", route_paths)
        
        # Clean up
        del sys.modules[module_name]
    
    def test_path_normalization(self):
        """Test path normalization."""
        # Create URL patterns with various path formats
        urlpatterns = [
            path("no-leading-slash", index_view, name="no-leading"),
            path("/with-leading-slash", index_view, name="with-leading"),
            path("trailing-slash/", index_view, name="trailing"),
            path("//double//slashes//", index_view, name="double"),
        ]
        
        # Create a router and resolver
        router = APIRouter()
        resolver = URLResolver(router)
        
        # Register the patterns
        resolver.register(urlpatterns)
        
        # Check that the paths were normalized
        route_paths = [route.path for route in router.routes]
        self.assertIn("/no-leading-slash", route_paths)
        self.assertIn("/with-leading-slash", route_paths)
        self.assertIn("/trailing-slash", route_paths)
        self.assertIn("/double/slashes", route_paths)
    
    def test_path_parameters(self):
        """Test path parameter conversion."""
        # Create URL patterns with various parameter formats
        urlpatterns = [
            path("/int/<int:id>", detail_view, name="int-param"),
            path("/str/<str:name>", detail_view, name="str-param"),
            path("/slug/<slug:slug>", detail_view, name="slug-param"),
            path("/uuid/<uuid:uuid>", detail_view, name="uuid-param"),
            path("/path/<path:path>", detail_view, name="path-param"),
            path("/multi/<int:id>/<str:name>", detail_view, name="multi-param"),
        ]
        
        # Create a router and resolver
        router = APIRouter()
        resolver = URLResolver(router)
        
        # Register the patterns
        resolver.register(urlpatterns)
        
        # Check that the parameters were converted
        route_paths = [route.path for route in router.routes]
        self.assertIn("/int/{id}", route_paths)
        self.assertIn("/str/{name}", route_paths)
        self.assertIn("/slug/{slug}", route_paths)
        self.assertIn("/uuid/{uuid}", route_paths)
        self.assertIn("/path/{path}", route_paths)
        self.assertIn("/multi/{id}/{name}", route_paths)


def run_tests():
    """Run the URL configuration tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 