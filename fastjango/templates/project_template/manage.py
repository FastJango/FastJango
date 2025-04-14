#!/usr/bin/env python
"""
FastJango's command-line utility for administrative tasks.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{{project_name_snake}}.settings")
    try:
        from fastjango.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import FastJango. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main() 