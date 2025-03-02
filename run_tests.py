
#!/usr/bin/env python3
"""
Test runner script for WildOakDealsApp.
Runs all tests and generates a report.
"""
import sys
import os
import argparse
import subprocess
import pytest
import datetime

def ensure_dependencies():
    """Check and install any missing dependencies for tests."""
    try:
        import bs4
        print("BeautifulSoup is already installed.")
    except ImportError:
        print("Installing BeautifulSoup for tests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        print("BeautifulSoup installed successfully.")

def run_tests(pattern=None, verbose=True):
    """Run tests and generate a report."""
    print("Running tests for WildOakDealsApp...")
    # Create test reports directory if it doesn't exist
    if not os.path.exists('test_reports'):
        os.makedirs('test_reports')
    
    # Generate timestamp for the report file name
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f'test_reports/test_report_{timestamp}.txt'
    print(f"Generating report in {report_file}")
    
    # Build pytest arguments
    pytest_args = ['-v'] if verbose else []
    if pattern:
        pytest_args.append(pattern)
    
    # Run pytest and capture output to file
    with open(report_file, 'w') as f:
        try:
            exit_code = pytest.main(pytest_args)
            f.write(f"Test run complete.\nExit code: {exit_code}\n")
            if exit_code == 0:
                f.write("All tests passed! ✅\n")
            else:
                f.write("Some tests failed. ❌\n")
            print(f"Test run complete.\nExit code: {exit_code}")
            if exit_code == 0:
                print("All tests passed! ✅")
            else:
                print("Some tests failed. ❌")
            return exit_code
        except Exception as e:
            error_msg = f"Error running tests: {str(e)}"
            f.write(error_msg + "\n")
            print(error_msg)
            return 1

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
