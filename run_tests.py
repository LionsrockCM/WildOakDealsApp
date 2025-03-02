
#!/usr/bin/env python3
"""
Test runner script for WildOakDealsApp.
Runs all tests and generates a report.
"""
import pytest
import os
import sys
from datetime import datetime

# Create directories if they don't exist
os.makedirs('tests', exist_ok=True)
os.makedirs('test_reports', exist_ok=True)

# Create __init__.py files to make directories into packages
with open('tests/__init__.py', 'w') as f:
    f.write('# Tests package\n')

def main():
    """Run all tests and generate a report."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f'test_reports/test_report_{timestamp}.txt'
    
    print(f"Running tests for WildOakDealsApp...")
    print(f"Generating report in {report_file}")
    
    # Run the tests
    exit_code = pytest.main([
        '-v',
        'tests/',
        f'--tb=native',
        '--color=yes'
    ])
    
    # Print summary
    print("\nTest run complete.")
    print(f"Exit code: {exit_code}")
    
    if exit_code == 0:
        print("All tests passed! ✅")
    else:
        print("Some tests failed. ❌")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())
