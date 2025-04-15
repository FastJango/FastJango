#!/usr/bin/env python
"""
Tests for FastJango settings configuration.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango settings components
from fastjango.conf import settings, LazySettings, Settings, ImproperlyConfigured


class SettingsTest(unittest.TestCase):
    """Test suite for settings configuration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for a settings module
        self.temp_dir = tempfile.mkdtemp()
        sys.path.insert(0, self.temp_dir)
        
        # Create a test settings module
        self.settings_module = os.path.join(self.temp_dir, "test_settings_module.py")
        with open(self.settings_module, "w") as f:
            f.write("""
# Test settings module
DEBUG = True
SECRET_KEY = 'test-secret-key'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
INSTALLED_APPS = [
    'app1',
    'app2',
]
DATABASE = {
    'default': {
        'ENGINE': 'sqlite',
        'NAME': 'db.sqlite3',
    }
}
MIDDLEWARE = []
TEMPLATES = [{
    'BACKEND': 'fastjango.template.backends.jinja2.Jinja2',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [],
    }
}]
STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'
""")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and settings module
        sys.path.remove(self.temp_dir)
        os.unlink(self.settings_module)
        os.rmdir(self.temp_dir)
    
    def test_lazy_settings(self):
        """Test LazySettings functionality."""
        # Create LazySettings with our test module
        lazy_settings = LazySettings()
        lazy_settings.configure(
            settings_module="test_settings_module"
        )
        
        # Test that settings are loaded correctly
        self.assertTrue(lazy_settings.DEBUG)
        self.assertEqual(lazy_settings.SECRET_KEY, 'test-secret-key')
        self.assertEqual(lazy_settings.ALLOWED_HOSTS, ['localhost', '127.0.0.1'])
        self.assertEqual(lazy_settings.INSTALLED_APPS, ['app1', 'app2'])
        self.assertEqual(lazy_settings.DATABASE['default']['ENGINE'], 'sqlite')
    
    def test_direct_settings(self):
        """Test direct Settings functionality."""
        # Create Settings directly
        direct_settings = Settings("test_settings_module")
        
        # Test that settings are loaded correctly
        self.assertTrue(direct_settings.DEBUG)
        self.assertEqual(direct_settings.SECRET_KEY, 'test-secret-key')
        self.assertEqual(direct_settings.ALLOWED_HOSTS, ['localhost', '127.0.0.1'])
        self.assertEqual(direct_settings.INSTALLED_APPS, ['app1', 'app2'])
        self.assertEqual(direct_settings.DATABASE['default']['ENGINE'], 'sqlite')
    
    def test_settings_modification(self):
        """Test that settings can be modified."""
        # Create Settings
        settings_obj = Settings("test_settings_module")
        
        # Modify a setting
        settings_obj.DEBUG = False
        self.assertFalse(settings_obj.DEBUG)
        
        # Add a new setting
        settings_obj.NEW_SETTING = 'new-value'
        self.assertEqual(settings_obj.NEW_SETTING, 'new-value')
    
    def test_settings_as_dict(self):
        """Test settings as a dictionary."""
        # Create Settings
        settings_obj = Settings("test_settings_module")
        
        # Convert to dictionary
        settings_dict = settings_obj.as_dict()
        
        # Check dictionary values
        self.assertTrue(settings_dict['DEBUG'])
        self.assertEqual(settings_dict['SECRET_KEY'], 'test-secret-key')
        self.assertEqual(settings_dict['ALLOWED_HOSTS'], ['localhost', '127.0.0.1'])
    
    def test_missing_settings(self):
        """Test behavior with missing settings."""
        # Create Settings
        settings_obj = Settings("test_settings_module")
        
        # Try to access a non-existent setting
        with self.assertRaises(AttributeError):
            value = settings_obj.NON_EXISTENT_SETTING
    
    def test_required_settings(self):
        """Test required settings."""
        # Create a settings module missing SECRET_KEY
        no_secret_settings = os.path.join(self.temp_dir, "no_secret_settings.py")
        with open(no_secret_settings, "w") as f:
            f.write("""
# Missing SECRET_KEY
DEBUG = True
ALLOWED_HOSTS = ['localhost']
""")
        
        # Create Settings object that checks for required settings
        def create_settings():
            settings_obj = Settings("no_secret_settings")
            settings_obj.validate_settings(['SECRET_KEY'])
        
        # Check that validation raises ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured):
            create_settings()
    
    def test_default_settings(self):
        """Test default settings."""
        # Create minimal settings module
        minimal_settings = os.path.join(self.temp_dir, "minimal_settings.py")
        with open(minimal_settings, "w") as f:
            f.write("""
# Minimal settings
SECRET_KEY = 'minimal-key'
""")
        
        # Create Settings with defaults
        settings_obj = Settings("minimal_settings")
        
        # Set default values
        settings_obj.set_defaults({
            'DEBUG': False,
            'ALLOWED_HOSTS': ['localhost'],
            'INSTALLED_APPS': [],
        })
        
        # Check that defaults were applied
        self.assertFalse(settings_obj.DEBUG)
        self.assertEqual(settings_obj.ALLOWED_HOSTS, ['localhost'])
        self.assertEqual(settings_obj.INSTALLED_APPS, [])
        
        # Original setting should still be there
        self.assertEqual(settings_obj.SECRET_KEY, 'minimal-key')


class GlobalSettingsTest(unittest.TestCase):
    """Test suite for global settings instance."""
    
    def test_global_settings(self):
        """Test the global settings object."""
        # The global settings object should be a LazySettings instance
        self.assertIsInstance(settings, LazySettings)
        
        # Try to access a setting (will use FASTJANGO_SETTINGS_MODULE if set)
        try:
            value = settings.SECRET_KEY
            # If we get here, a setting was found
            self.assertTrue(True)
        except (AttributeError, ImproperlyConfigured):
            # This is acceptable if no settings module is configured
            pass


def run_tests():
    """Run the settings tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()
