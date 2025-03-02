
#!/usr/bin/env python3
"""
Test runner script for WildOakDealsApp.
Runs all tests and generates a report.
"""
import sys
import os
import argparse
import subprocess
import datetime

def ensure_dependencies():
    """Check and install any missing dependencies for tests."""
    required_packages = ['pytest', 'beautifulsoup4', 'pytest-flask']
    for package in required_packages:
        try:
            __import__(package.split('-')[0])
            print(f"{package} is already installed.")
        except ImportError:
            print(f"Installing {package} for tests...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} installed successfully.")

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
    
    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest"]
    if verbose:
        pytest_cmd.append("-v")
    if pattern:
        pytest_cmd.append(pattern)
    
    # Capture output to file
    with open(report_file, 'w') as f:
        try:
            process = subprocess.run(pytest_cmd, capture_output=True, text=True, cwd=os.getcwd())
            f.write(process.stdout)
            f.write(process.stderr)
            f.write(f"\nTest run complete.\nExit code: {process.returncode}\n")
            
            if process.returncode == 0:
                f.write("All tests passed! ✅\n")
                print("All tests passed! ✅")
            else:
                f.write("Some tests failed. ❌\n")
                print("Some tests failed. ❌")
                
            print(f"Test run complete.\nExit code: {process.returncode}")
            print(process.stdout)
            print(process.stderr)
            return process.returncode
            
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
