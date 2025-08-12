#!/usr/bin/env python
"""
Tests for FastJango HTTP response classes.
"""

import os
import sys
import json
import unittest
from typing import Dict, Any

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango HTTP components
from fastjango.http import (
    HttpResponse,
    JsonResponse,
    TemplateResponse,
    redirect,
)


class HttpResponseTest(unittest.TestCase):
    """Test suite for HttpResponse class."""
    
    def test_basic_response(self):
        """Test basic HttpResponse functionality."""
        response = HttpResponse("Hello, world!")
        self.assertEqual(response.body, b"Hello, world!")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_custom_status_code(self):
        """Test HttpResponse with custom status code."""
        response = HttpResponse("Created", status_code=201)
        self.assertEqual(response.status_code, 201)
        
    def test_custom_headers(self):
        """Test HttpResponse with custom headers."""
        response = HttpResponse(
            content="Test",
            headers={"X-Custom-Header": "Value"}
        )
        self.assertEqual(response.headers.get("X-Custom-Header"), "Value")
        
    def test_content_type(self):
        """Test HttpResponse with custom content type."""
        response = HttpResponse("Text content", media_type="text/plain")
        self.assertIn("text/plain", response.headers.get("content-type", ""))


class JsonResponseTest(unittest.TestCase):
    """Test suite for JsonResponse class."""
    
    def test_basic_json_response(self):
        """Test basic JsonResponse functionality."""
        data = {"message": "Hello", "count": 42}
        response = JsonResponse(data)
        self.assertIn("application/json", response.headers.get("content-type", ""))
        
        # Parse the JSON body
        body_dict = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body_dict, data)
        
    def test_json_with_custom_status(self):
        """Test JsonResponse with custom status code."""
        data = {"error": "Not found"}
        response = JsonResponse(data, status_code=404)
        self.assertEqual(response.status_code, 404)
        
    def test_json_with_non_dict(self):
        """Test JsonResponse with non-dict data."""
        data = [1, 2, 3, 4]
        response = JsonResponse(data)
        body_list = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body_list, data)


class RedirectResponseTest(unittest.TestCase):
    """Test suite for redirect helper."""
    
    def test_temporary_redirect(self):
        """Test temporary (302) redirect."""
        response = redirect("/new-location")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("location"), "/new-location")
        
    def test_permanent_redirect(self):
        """Test permanent (301) redirect."""
        response = redirect("/permanent", permanent=True)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers.get("location"), "/permanent")




def run_tests():
    """Run the HTTP response tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 