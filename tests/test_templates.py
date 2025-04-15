#!/usr/bin/env python
"""
Tests for FastJango template rendering functionality.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango template components
from fastjango.templates import Template, get_template, render_to_string
from fastjango.template.loaders import FileSystemLoader, PackageLoader
from fastjango.template.context import Context


class TemplateTest(unittest.TestCase):
    """Test suite for template functionality."""
    
    def setUp(self):
        """Set up test environment with temporary template directory."""
        # Create a temporary directory for templates
        self.template_dir = tempfile.mkdtemp()
        
        # Create some test templates
        self.create_template("base.html", """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{% block title %}Default Title{% endblock %}</title>
        </head>
        <body>
            <header>
                <h1>{% block header %}Header{% endblock %}</h1>
            </header>
            <main>
                {% block content %}{% endblock %}
            </main>
            <footer>
                {% block footer %}Footer{% endblock %}
            </footer>
        </body>
        </html>
        """)
        
        self.create_template("page.html", """
        {% extends "base.html" %}
        
        {% block title %}My Page{% endblock %}
        
        {% block header %}Welcome to My Page{% endblock %}
        
        {% block content %}
            <p>This is the content of my page.</p>
            <p>Hello, {{ name }}!</p>
            
            {% if show_list %}
                <ul>
                {% for item in items %}
                    <li>{{ item }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endblock %}
        """)
        
        self.create_template("simple.html", "Hello, {{ name }}!")
        
        # Initialize the template loader
        self.loader = FileSystemLoader(self.template_dir)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.template_dir)
    
    def create_template(self, name, content):
        """Create a template file in the temporary directory."""
        template_path = os.path.join(self.template_dir, name)
        with open(template_path, "w") as f:
            f.write(content)
    
    def test_simple_template(self):
        """Test rendering a simple template."""
        template = Template("Hello, {{ name }}!")
        context = {"name": "World"}
        rendered = template.render(context)
        self.assertEqual(rendered, "Hello, World!")
    
    def test_template_with_loop(self):
        """Test rendering a template with a loop."""
        template = Template("""
        <ul>
        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
        """)
        context = {"items": ["apple", "banana", "cherry"]}
        rendered = template.render(context)
        
        # Normalize whitespace for comparison
        rendered = " ".join(rendered.split())
        expected = "<ul> <li>apple</li> <li>banana</li> <li>cherry</li> </ul>"
        self.assertEqual(rendered, expected)
    
    def test_template_with_conditional(self):
        """Test rendering a template with conditionals."""
        template = Template("""
        {% if show_greeting %}
            <p>Hello, {{ name }}!</p>
        {% else %}
            <p>No greeting.</p>
        {% endif %}
        """)
        
        # Test with show_greeting=True
        context1 = {"show_greeting": True, "name": "World"}
        rendered1 = " ".join(template.render(context1).split())
        self.assertEqual(rendered1, "<p>Hello, World!</p>")
        
        # Test with show_greeting=False
        context2 = {"show_greeting": False, "name": "World"}
        rendered2 = " ".join(template.render(context2).split())
        self.assertEqual(rendered2, "<p>No greeting.</p>")
    
    def test_template_inheritance(self):
        """Test template inheritance."""
        # Load the template from the file system
        template = self.loader.get_template("page.html")
        
        # Render with context
        context = {
            "name": "John",
            "show_list": True,
            "items": ["Item 1", "Item 2", "Item 3"]
        }
        rendered = template.render(context)
        
        # Check that blocks from the parent template are present
        self.assertIn("<title>My Page</title>", rendered)
        self.assertIn("<h1>Welcome to My Page</h1>", rendered)
        
        # Check that the content block has been filled
        self.assertIn("<p>This is the content of my page.</p>", rendered)
        self.assertIn("<p>Hello, John!</p>", rendered)
        
        # Check that the loop rendered correctly
        self.assertIn("<li>Item 1</li>", rendered)
        self.assertIn("<li>Item 2</li>", rendered)
        self.assertIn("<li>Item 3</li>", rendered)
    
    def test_get_template(self):
        """Test the get_template function."""
        # Set up the template directory in settings
        import fastjango.conf
        fastjango.conf.settings.TEMPLATES = [{
            "BACKEND": "fastjango.template.backends.jinja2.Jinja2",
            "DIRS": [self.template_dir],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": []
            }
        }]
        
        # Get a template
        template = get_template("simple.html")
        rendered = template.render({"name": "World"})
        self.assertEqual(rendered, "Hello, World!")
    
    def test_render_to_string(self):
        """Test the render_to_string function."""
        # Set up the template directory in settings
        import fastjango.conf
        fastjango.conf.settings.TEMPLATES = [{
            "BACKEND": "fastjango.template.backends.jinja2.Jinja2",
            "DIRS": [self.template_dir],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": []
            }
        }]
        
        # Render a template to string
        rendered = render_to_string("simple.html", {"name": "World"})
        self.assertEqual(rendered, "Hello, World!")


class TemplateResponseTest(unittest.TestCase):
    """Test suite for TemplateResponse."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for templates
        self.template_dir = tempfile.mkdtemp()
        
        # Create a test template
        self.create_template("response.html", """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
        </head>
        <body>
            <h1>{{ title }}</h1>
            <p>{{ message }}</p>
        </body>
        </html>
        """)
        
        # Set up the template directory in settings
        import fastjango.conf
        fastjango.conf.settings.TEMPLATES = [{
            "BACKEND": "fastjango.template.backends.jinja2.Jinja2",
            "DIRS": [self.template_dir],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": []
            }
        }]
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.template_dir)
    
    def create_template(self, name, content):
        """Create a template file in the temporary directory."""
        template_path = os.path.join(self.template_dir, name)
        with open(template_path, "w") as f:
            f.write(content)
    
    def test_template_response(self):
        """Test TemplateResponse."""
        from fastjango.template.response import TemplateResponse
        
        # Create a TemplateResponse
        context = {"title": "Test Page", "message": "Hello, World!"}
        response = TemplateResponse("response.html", context)
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, "response.html")
        self.assertEqual(response.context_data, context)
        
        # Render the response
        content = response.body.decode("utf-8")
        self.assertIn("<title>Test Page</title>", content)
        self.assertIn("<h1>Test Page</h1>", content)
        self.assertIn("<p>Hello, World!</p>", content)


def run_tests():
    """Run the template tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 