#!/usr/bin/env python
"""
Tests for FastJango CLI commands and arguments.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastJango CLI components
from fastjango import __version__
from typer.testing import CliRunner


class CLITest(unittest.TestCase):
    """Test suite for CLI functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.runner = CliRunner(mix_stderr=False)
    
    def test_version_flag(self):
        """Test --version flag displays the correct version and exits."""
        # Import locally to avoid module-level imports during patch setup
        from fastjango.cli.main import app
        
        # Run with --version flag
        with patch("typer.Exit") as mock_exit:
            result = self.runner.invoke(app, ["--version"])
            
            # Check that exit was called once
            self.assertEqual(mock_exit.call_count, 1)
            
            # Check version output in console.print call
            self.assertIn(f"FastJango v{__version__}", result.stdout)
    
    def test_help_command(self):
        """Test help command displays proper help information."""
        # Import locally to use freshly instantiated app in this test
        from fastjango.cli.main import app
        
        # Run with --help flag
        result = self.runner.invoke(app, ["--help"])
        
        # Check that help text is displayed
        self.assertEqual(result.exit_code, 0)
        self.assertIn("FastJango command-line utility for administrative tasks", result.stdout)
        
        # Check that commands are listed
        self.assertIn("startproject", result.stdout)
        self.assertIn("startapp", result.stdout)
        self.assertIn("runserver", result.stdout)
    
    def test_command_help(self):
        """Test command-specific help displays proper information."""
        # Import locally to use freshly instantiated app in this test
        from fastjango.cli.main import app
        
        # Test help for startproject command
        result = self.runner.invoke(app, ["startproject", "--help"])
        
        # Check that command help is displayed
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Creates a new FastJango project with the given name", result.stdout)
        self.assertIn("--directory", result.stdout)
        
        # Test help for startapp command
        result = self.runner.invoke(app, ["startapp", "--help"])
        
        # Check that command help is displayed
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Creates a new app in the current FastJango project", result.stdout)
        
        # Test help for runserver command
        result = self.runner.invoke(app, ["runserver", "--help"])
        
        # Check that command help is displayed
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Runs the FastJango development server", result.stdout)
        self.assertIn("--host", result.stdout)
        self.assertIn("--port", result.stdout)
    
    def test_verbose_flag(self):
        """Test --verbose flag enables debug logging."""
        # Import locally to avoid module-level imports during patch setup
        from fastjango.cli.main import app
        import logging
        
        # Patch setup_logging to verify DEBUG level is used
        with patch("fastjango.core.logging.setup_logging") as mock_setup_logging:
            # Also patch the logger.debug method to verify the message
            with patch("fastjango.cli.main.logger.debug") as mock_debug:
                result = self.runner.invoke(app, ["--verbose"])
                
                # Check that setup_logging was called with DEBUG level
                mock_setup_logging.assert_called_once_with(logging.DEBUG)
                
                # Verify that "Verbose logging enabled" debug message was logged
                mock_debug.assert_called_once_with("Verbose logging enabled")
                
                # Check command completed successfully
                self.assertEqual(result.exit_code, 0)


def run_tests():
    """Run the CLI tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 