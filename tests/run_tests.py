#!/usr/bin/env python
"""
Main test runner for FastJango.
"""

import os
import sys
import shutil
import unittest
import argparse
import importlib.util
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Known test fixture directories that should be cleaned up
TEST_FIXTURE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_app"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "nested_app"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_cases"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_settings.py"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_urls.py"),
]

def load_tests_from_module(module_path):
    """
    Load tests from a module file path.
    """
    module_name = os.path.basename(module_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get all test cases
    test_cases = []
    for item_name in dir(module):
        item = getattr(module, item_name)
        if isinstance(item, type) and issubclass(item, unittest.TestCase):
            test_cases.append(item)
    
    return test_cases


def discover_test_modules(test_dir=None):
    """
    Discover all test modules in the given directory.
    
    Args:
        test_dir: Directory to search for test modules. Defaults to current directory.
        
    Returns:
        List of file paths to test modules.
    """
    if test_dir is None:
        test_dir = os.path.dirname(os.path.abspath(__file__))
    
    test_files = []
    for file in os.listdir(test_dir):
        if (file.startswith("test_") and file.endswith(".py") and
                not file == os.path.basename(__file__)):
            test_files.append(os.path.join(test_dir, file))
    
    return sorted(test_files)


def run_tests(test_modules=None, verbosity=1):
    """
    Run tests from the given modules.
    
    Args:
        test_modules: List of module paths to run tests from.
        verbosity: Verbosity level for test output.
        
    Returns:
        Test result.
    """
    # Discover test modules if not provided
    if test_modules is None:
        test_modules = discover_test_modules()
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests from each module
    loader = unittest.defaultTestLoader
    for module_path in test_modules:
        try:
            test_cases = load_tests_from_module(module_path)
            for test_case in test_cases:
                suite.addTests(loader.loadTestsFromTestCase(test_case))
            print(f"Loaded tests from {os.path.basename(module_path)}")
        except Exception as e:
            print(f"Error loading tests from {module_path}: {e}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def ensure_cleanup():
    """
    Ensure that all test fixtures are cleaned up after tests run.
    This is a safety measure in case individual test tearDown methods fail.
    """
    print("\nPerforming final cleanup of test fixtures...")
    for path in TEST_FIXTURE_PATHS:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Cleaned up directory: {os.path.basename(path)}")
            elif os.path.exists(path):
                os.remove(path)
                print(f"Cleaned up file: {os.path.basename(path)}")
        except Exception as e:
            # Just log the error but don't stop the cleanup process
            print(f"Error during cleanup of {path}: {e}")


def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description="Run FastJango tests.")
    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        default=1,
        help="Verbosity level (1-3)"
    )
    parser.add_argument(
        "-f", "--filter",
        type=str,
        help="Filter tests by name (e.g. test_urls)"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available test modules"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of test fixtures (useful for debugging)"
    )
    
    args = parser.parse_args()
    
    # Discover test modules
    test_modules = discover_test_modules()
    
    # List test modules if requested
    if args.list:
        print("Available test modules:")
        for module in test_modules:
            print(f"  {os.path.basename(module)}")
        return 0
    
    # Filter test modules if requested
    if args.filter:
        test_modules = [
            module for module in test_modules 
            if args.filter in os.path.basename(module)
        ]
        
        if not test_modules:
            print(f"No test modules matching filter: {args.filter}")
            return 1
    
    try:
        # Run tests
        print(f"\nRunning FastJango tests...\n")
        result = run_tests(test_modules, args.verbosity)
        
        # Output summary
        print("\nTest Summary:")
        print(f"  Ran {result.testsRun} tests")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Skipped: {len(result.skipped)}")
        
        return 0 if result.wasSuccessful() else 1
    finally:
        # Always clean up test fixtures unless explicitly disabled
        if not args.no_cleanup:
            ensure_cleanup()


if __name__ == "__main__":
    sys.exit(main()) 