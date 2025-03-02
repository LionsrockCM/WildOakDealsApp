#!/usr/bin/env python3
"""
Test runner script for WildOakDealsApp.
Runs all tests and generates a report.
"""
import sys
import os
import argparse
from test_utils import run_tests, create_test_file

def main():
    parser = argparse.ArgumentParser(description='Run tests for WildOakDealsApp')
    parser.add_argument('--pattern', help='Pattern to match test files')
    parser.add_argument('--quiet', action='store_true', help='Run with less output')
    args = parser.parse_args()

    return run_tests(pattern=args.pattern, verbose=not args.quiet)

if __name__ == '__main__':
    sys.exit(main())