#!/usr/bin/env python
"""
Tests for FastJango app configuration functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango app configuration components
from fastjango.apps import AppConfig
from fastjango.apps.registry import Apps, apps


class CustomAppConfig(AppConfig):
    """Custom app configuration for testing."""
    
    name = "test_app"
    verbose_name = "Test App"
    
    def ready(self):
        """App is ready callback."""
        self.ready_called = True


class SimpleAppConfig(AppConfig):
    """Simple app configuration for testing."""
    
    name = "simple_app"


class AppConfigTest(unittest.TestCase):
    """Test suite for AppConfig classes."""
    
    def test_basic_app_config(self):
        """Test basic AppConfig functionality."""
        # Create an AppConfig instance
        app_config = AppConfig(app_name="test_app", app_module=None)
        
        # Check attributes
        self.assertEqual(app_config.name, "test_app")
        self.assertEqual(app_config.verbose_name, "Test App")  # Should auto-convert
        self.assertEqual(app_config.label, "test_app")
        
        # Check get_model returns None for invalid model
        self.assertIsNone(app_config.get_model("NonExistentModel"))
    
    def test_custom_app_config(self):
        """Test custom AppConfig subclass."""
        # Create a custom AppConfig instance
        app_config = CustomAppConfig(app_name="test_app", app_module=None)
        
        # Check attributes
        self.assertEqual(app_config.name, "test_app")
        self.assertEqual(app_config.verbose_name, "Test App")
        
        # Call ready and check that it was called
        app_config.ready()
        self.assertTrue(hasattr(app_config, "ready_called"))
        self.assertTrue(app_config.ready_called)
    
    def test_app_config_label(self):
        """Test deriving app label from name."""
        # Full module path
        app_config1 = AppConfig(app_name="project.apps.myapp", app_module=None)
        self.assertEqual(app_config1.label, "myapp")
        
        # Simple name
        app_config2 = AppConfig(app_name="myapp", app_module=None)
        self.assertEqual(app_config2.label, "myapp")
    
    def test_get_models(self):
        """Test getting models from an app."""
        # Create a mock app module with models
        class MockModel1:
            pass
        
        class MockModel2:
            pass
        
        # Create a mock module
        mock_module = MagicMock()
        mock_module.MockModel1 = MockModel1
        mock_module.MockModel2 = MockModel2
        
        # Create app config with models
        app_config = AppConfig(app_name="test_app", app_module=mock_module)
        app_config.models = {"mockmodel1": MockModel1, "mockmodel2": MockModel2}
        
        # Check get_models
        models = app_config.get_models()
        self.assertEqual(len(models), 2)
        self.assertIn(MockModel1, models)
        self.assertIn(MockModel2, models)
        
        # Check get_model
        self.assertEqual(app_config.get_model("MockModel1"), MockModel1)
        self.assertEqual(app_config.get_model("mockmodel1"), MockModel1)  # Case insensitive


class AppsRegistryTest(unittest.TestCase):
    """Test suite for Apps registry."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a fresh Apps registry
        self.apps = Apps()
    
    def test_register_app_config(self):
        """Test registering an app configuration."""
        # Create and register an app config
        app_config = SimpleAppConfig(app_name="simple_app", app_module=None)
        self.apps.register_app_config(app_config)
        
        # Check that the app is registered
        self.assertIn("simple_app", self.apps.app_configs)
        self.assertEqual(self.apps.app_configs["simple_app"], app_config)
    
    def test_get_app_config(self):
        """Test getting an app configuration."""
        # Create and register an app config
        app_config = SimpleAppConfig(app_name="simple_app", app_module=None)
        self.apps.register_app_config(app_config)
        
        # Check that get_app_config returns the correct AppConfig
        self.assertEqual(self.apps.get_app_config("simple_app"), app_config)
        
        # Check that get_app_config raises LookupError for unknown app
        with self.assertRaises(LookupError):
            self.apps.get_app_config("unknown_app")
    
    def test_is_installed(self):
        """Test checking if an app is installed."""
        # Create and register an app config
        app_config = SimpleAppConfig(app_name="simple_app", app_module=None)
        self.apps.register_app_config(app_config)
        
        # Check that is_installed returns True for installed app
        self.assertTrue(self.apps.is_installed("simple_app"))
        
        # Check that is_installed returns False for unknown app
        self.assertFalse(self.apps.is_installed("unknown_app"))
    
    def test_get_model(self):
        """Test getting a model."""
        # Create a mock model
        class MockModel:
            pass
        
        # Create and register an app config with the model
        app_config = SimpleAppConfig(app_name="simple_app", app_module=None)
        app_config.models = {"mockmodel": MockModel}
        self.apps.register_app_config(app_config)
        
        # Check that get_model returns the correct model
        self.assertEqual(
            self.apps.get_model("simple_app", "MockModel"),
            MockModel
        )
        
        # Check that get_model returns None for unknown model
        self.assertIsNone(self.apps.get_model("simple_app", "UnknownModel"))
        
        # Check that get_model raises LookupError for unknown app
        with self.assertRaises(LookupError):
            self.apps.get_model("unknown_app", "MockModel")
    
    def test_populate(self):
        """Test populating apps from installed apps setting."""
        # Mock settings with INSTALLED_APPS
        with patch("fastjango.conf.settings") as mock_settings:
            mock_settings.INSTALLED_APPS = [
                "tests.test_app",
                "simple_app",
            ]
            
            # Mock importlib
            with patch("importlib.import_module") as mock_import:
                # Mock imported modules
                mock_test_app = MagicMock()
                mock_test_app.default_app_config = "tests.test_app.apps.TestAppConfig"
                
                mock_test_app_apps = MagicMock()
                mock_test_app_apps.TestAppConfig = CustomAppConfig
                
                mock_simple_app = MagicMock()
                
                # Configure import_module to return our mocks
                def mock_import_side_effect(name):
                    if name == "tests.test_app":
                        return mock_test_app
                    elif name == "tests.test_app.apps":
                        return mock_test_app_apps
                    elif name == "simple_app":
                        return mock_simple_app
                    raise ImportError(f"No module named '{name}'")
                
                mock_import.side_effect = mock_import_side_effect
                
                # Call populate
                self.apps.populate(settings=mock_settings)
                
                # Check that the apps are registered
                self.assertIn("test_app", self.apps.app_configs)
                self.assertIn("simple_app", self.apps.app_configs)
                
                # Check that the correct AppConfig classes were used
                self.assertIsInstance(self.apps.app_configs["test_app"], CustomAppConfig)
                self.assertIsInstance(self.apps.app_configs["simple_app"], AppConfig)


class SingletonAppsTest(unittest.TestCase):
    """Test suite for the singleton apps instance."""
    
    def test_singleton_apps(self):
        """Test that apps is a singleton."""
        # The global apps object should be an Apps instance
        self.assertIsInstance(apps, Apps)
        
        # Creating a new Apps instance should not replace the singleton
        new_apps = Apps()
        self.assertIsNot(new_apps, apps)


def run_tests():
    """Run the app configuration tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 