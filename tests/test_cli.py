#!/usr/bin/env python
"""
Tests for FastJango CLI commands and arguments.
"""

import os
import sys
import unittest
from typer.testing import CliRunner

# Add project root to path if script is run from tests directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastjango import __version__
from typer.main import get_command


class CLITest(unittest.TestCase):
    """Test suite for CLI functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_version_flag(self):
        """Test version subcommand displays the correct version and exits."""
        from fastjango.cli.main import app
        
        result = self.runner.invoke(app, ["version"])  # prints then exits(0)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(f"FastJango v{__version__}", result.stdout)
    
    def test_command_registry(self):
        """Verify core commands are registered in the CLI."""
        from fastjango.cli.main import app
        click_cmd = get_command(app)
        commands = click_cmd.list_commands(None)
        # Ensure key commands exist
        for name in ["startproject", "startapp", "runserver", "makemigrations", "migrate", "shell", "version"]:
            self.assertIn(name, commands)


def run_tests():
    """Run the CLI tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests() 