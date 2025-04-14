"""
Tests for {{app_name}} routes.
"""

import pytest
from fastapi.testclient import TestClient
from fastjango.test import TestCase

from ..routes import router


class {{app_name_camel}}RoutesTests(TestCase):
    """
    Tests for {{app_name_camel}} routes.
    """
    
    def setUp(self):
        """
        Set up test client.
        """
        self.client = TestClient(router)
        
    def test_list_{{app_name_snake}}s(self):
        """
        Test listing {{app_name_camel}}s.
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
    def test_create_{{app_name_snake}}(self):
        """
        Test creating a {{app_name_camel}}.
        """
        data = {
            "name": "Test {{app_name_camel}}",
            "description": "This is a test"
        }
        response = self.client.post("/", json=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], data["name"]) 