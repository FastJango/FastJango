#!/usr/bin/env python
"""
FastJango command-line utility for administrative tasks.
"""

import os
import sys

if __name__ == "__main__":
    try:
        from fastjango.cli.main import cli
        cli()
    except ImportError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.stderr.write(
            "Make sure FastJango is installed and available on your PYTHONPATH.\n"
            "Try running 'pip install fastjango' or 'pip install -e .' if in development mode.\n"
        )
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1) 