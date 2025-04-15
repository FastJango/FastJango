#!/usr/bin/env python
"""
Clean up test fixtures that might be left over from test runs.
"""

import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test fixture paths to clean up
TEST_FIXTURE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_app"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "nested_app"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_cases"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_settings.py"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_urls.py"),
]

def cleanup_fixtures():
    """
    Clean up all test fixtures.
    """
    print("Cleaning up test fixtures...")
    
    for path in TEST_FIXTURE_PATHS:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Removed directory: {os.path.basename(path)}")
            elif os.path.exists(path):
                os.remove(path)
                print(f"Removed file: {os.path.basename(path)}")
        except Exception as e:
            print(f"Error removing {path}: {e}")
    
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup_fixtures() 