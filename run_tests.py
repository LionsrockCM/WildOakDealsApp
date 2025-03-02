#!/usr/bin/env python3
"""
Test runner script for WildOakDealsApp.
Runs all tests and generates a report.
"""
import sys
import os
import argparse
import subprocess
from test_utils import run_tests, create_test_file

def ensure_dependencies():
    """Check and install any missing dependencies for tests."""
    try:
        import bs4
        print("BeautifulSoup is already installed.")
    except ImportError:
        print("Installing BeautifulSoup for tests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        print("BeautifulSoup installed successfully.")

def main():
    parser = argparse.ArgumentParser(description='Run tests for WildOakDealsApp')
    parser.add_argument('--pattern', help='Pattern to match test files')
    parser.add_argument('--quiet', action='store_true', help='Run with less output')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation')
    args = parser.parse_args()
    
    if not args.skip_deps:
        ensure_dependencies()

    return run_tests(pattern=args.pattern, verbose=not args.quiet)

if __name__ == '__main__':
    sys.exit(main())