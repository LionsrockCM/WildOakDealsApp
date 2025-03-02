
#!/usr/bin/env python3
"""
Generate UI tests for WildOakDealsApp templates.
This script analyzes template files and creates test functions to verify UI elements.
"""
import os
import sys
import re
import argparse
from pathlib import Path
from test_utils import create_test_file

def extract_template_elements(template_path):
    """Extract key elements from a template file to generate tests for."""
    with open(template_path, 'r') as f:
        content = f.read()
    
    elements = {
        'title': re.search(r'<title>(.*?)</title>', content),
        'forms': re.findall(r'<form.*?id=[\'"]([^\'"]*)[\'"]', content),
        'inputs': re.findall(r'<input.*?id=[\'"]([^\'"]*)[\'"]', content),
        'buttons': re.findall(r'<button.*?>(.*?)</button>', content),
        'headers': re.findall(r'<h[1-6].*?>(.*?)</h[1-6]>', content),
    }
    
    # Extract non-empty values
    clean_elements = {}
    for key, value in elements.items():
        if isinstance(value, list):
            clean_elements[key] = [v for v in value if v]
        elif value:
            clean_elements[key] = value.group(1)
    
    return clean_elements

def generate_test_functions(template_name, elements):
    """Generate test functions based on template elements."""
    test_functions = []
    
    # Basic page test
    test_functions.append(f"test_{template_name}_page_loads")
    
    # Test form submission if forms exist
    if 'forms' in elements and elements['forms']:
        for form in elements['forms']:
            test_functions.append(f"test_{template_name}_{form}_submission")
    
    # Test UI elements
    test_functions.append(f"test_{template_name}_ui_elements")
    
    return test_functions

def main():
    parser = argparse.ArgumentParser(description='Generate UI tests for templates')
    parser.add_argument('template', help='Template file name (without path)')
    args = parser.parse_args()
    
    template_path = Path('templates') / args.template
    if not template_path.exists():
        print(f"Error: Template {args.template} not found in templates directory")
        return 1
    
    # Extract template name without extension
    template_name = args.template.split('.')[0]
    
    # Extract elements from template
    elements = extract_template_elements(template_path)
    
    # Generate test functions
    test_functions = generate_test_functions(template_name, elements)
    
    # Create the test file
    create_test_file(template_name, test_functions)
    
    print(f"Generated tests for {template_name}:")
    for func in test_functions:
        print(f"  - {func}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
