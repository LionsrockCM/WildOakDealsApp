
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
    """Run the test utility with command line arguments."""
    parser = argparse.ArgumentParser(description='WildOakDealsApp test runner')
    parser.add_argument('--create', metavar='MODULE', help='Create a test file for MODULE')
    parser.add_argument('--test-funcs', metavar='FUNCS', help='Comma-separated list of test functions to create')
    parser.add_argument('--run', metavar='PATTERN', help='Run tests matching PATTERN')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Create test directory and __init__.py if they don't exist
    os.makedirs('tests', exist_ok=True)
    init_file = os.path.join('tests', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Tests package\n')
    
    # Create test reports directory if it doesn't exist
    os.makedirs('test_reports', exist_ok=True)
    
    if args.create:
        test_funcs = []
        if args.test_funcs:
            test_funcs = args.test_funcs.split(',')
        create_test_file(args.create, test_funcs)
        return 0
    
    if args.run:
        return run_tests(args.run)
    
    if args.all or len(sys.argv) == 1:
        return run_tests()
    
    parser.print_help()
    return 1

if __name__ == '__main__':
    sys.exit(main())
