#!/usr/bin/env python3
"""
Test runner for WildOakDealsApp
Runs all tests and generates a report
"""
import os
import sys
import subprocess
import datetime
import importlib.util

def check_and_install_requirements():
    """Check if required packages are installed and install them if necessary."""
    required_packages = ['pytest', 'beautifulsoup4', 'pytest-flask']
    for package in required_packages:
        try:
            importlib.import_module(package.split('-')[0])
            print(f"{package} is already installed.")
        except ImportError:
            print(f"Installing {package} for tests...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def run_tests():
    """Run all tests and generate a report."""
    check_and_install_requirements()

    # Create directory for test reports if it doesn't exist
    os.makedirs("test_reports", exist_ok=True)

    # Generate timestamp for the report file
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f"test_reports/test_report_{timestamp}.txt"

    # Construct pytest command - added tests/test_ui_styling.py
    pytest_cmd = [
        sys.executable, "-m", "pytest", 
        "-v",  # Verbose output
        "tests/",  # Test directory
        "--no-header"  # Remove header to make output cleaner
    ]

    print(f"Running tests with command: {' '.join(pytest_cmd)}")
    print(f"Test report will be saved to: {report_file}")

    # Capture output to file
    with open(report_file, 'w') as f:
        try:
            process = subprocess.run(pytest_cmd, capture_output=True, text=True, cwd=os.getcwd())
            f.write(process.stdout)
            f.write(process.stderr)
            f.write(f"\nTest run complete.\nExit code: {process.returncode}\n")

            # Print summary to console
            print("\nTest results summary:")
            print(f"Exit code: {process.returncode}")

            # Print a simple summary of passed/failed tests
            if "failed" in process.stdout:
                for line in process.stdout.split('\n'):
                    if "FAILED" in line or "PASSED" in line:
                        print(line)
            else:
                print("All tests passed!")

        except Exception as e:
            error_msg = f"Error running tests: {str(e)}"
            f.write(error_msg)
            print(error_msg)

if __name__ == "__main__":
    run_tests()