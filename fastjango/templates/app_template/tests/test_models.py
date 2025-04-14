"""
Tests for {{app_name}} models.
"""

import pytest
from django.test import TestCase
from fastjango.core.exceptions import ValidationError

from ..models import {{app_name_camel}}Model


class {{app_name_camel}}ModelTests(TestCase):
    """
    Tests for {{app_name_camel}}Model.
    """
    
    def test_create_{{app_name_snake}}(self):
        """
        Test creating a {{app_name_camel}}.
        """
        obj = {{app_name_camel}}Model.objects.create(
            name="Test {{app_name_camel}}",
            description="This is a test"
        )
        self.assertEqual(obj.name, "Test {{app_name_camel}}")
        self.assertEqual(obj.description, "This is a test")
        
    def test_validation(self):
        """
        Test validation logic.
        """
        obj = {{app_name_camel}}Model(name="test")
        with self.assertRaises(ValidationError):
            obj.save() 