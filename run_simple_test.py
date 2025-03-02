
#!/usr/bin/env python3
"""
Simple test runner for WildOakDealsApp
Runs a specific test file or all tests
"""
import os
import sys
import subprocess

def main():
    """Run tests and display results directly."""
    if len(sys.argv) > 1:
        # Run a specific test file
        test_file = sys.argv[1]
        cmd = [sys.executable, "-m", "pytest", test_file, "-v"]
    else:
        # Run all tests
        cmd = [sys.executable, "-m", "pytest", "-v"]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
