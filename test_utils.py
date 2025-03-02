
"""
Test utilities to automate test case creation and execution.
"""
import os
import sys
import inspect
import datetime
import unittest
import pytest
from pathlib import Path

def create_test_file(module_name, test_functions=None):
    """
    Create a test file with default structure and specified test functions.
    
    Args:
        module_name (str): Name of the module to test (e.g., 'login', 'deal_detail')
        test_functions (list): List of test function names to include
    
    Returns:
        Path: Path to the created test file
    """
    if test_functions is None:
        test_functions = []
    
    test_dir = Path('tests')
    if not test_dir.exists():
        test_dir.mkdir()
    
    # Create __init__.py if it doesn't exist
    init_file = test_dir / '__init__.py'
    if not init_file.exists():
        with open(init_file, 'w') as f:
            f.write('# Tests package\n')
    
    # Create test file
    test_file = test_dir / f'test_{module_name}.py'
    
    template = f'''
import os
import sys
import pytest
from bs4 import BeautifulSoup

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create roles
            admin_role = Role(name='Admin')
            user_role = Role(name='User')
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.commit()
            
            # Create test user
            test_user = User(username='testuser', role_id=user_role.id)
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()
        
        yield client
        
        with app.app_context():
            db.drop_all()

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={{
        'username': username,
        'password': password
    }}, follow_redirects=True)

'''
    
    # Add test functions
    for func_name in test_functions:
        template += f'''
def {func_name}(client):
    """Test for {func_name}."""
    # TODO: Implement test
    assert True
'''
    
    with open(test_file, 'w') as f:
        f.write(template.strip())
    
    print(f"Created test file: {test_file}")
    return test_file

def run_tests(pattern=None, verbose=True):
    """
    Run tests matching the given pattern.
    
    Args:
        pattern (str): Pattern to match test files
        verbose (bool): Run with verbose output
    """
    args = ['tests/']
    if pattern:
        args = [f'tests/test_{pattern}.py']
    
    if verbose:
        args.append('-v')
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_dir = Path('test_reports')
    if not report_dir.exists():
        report_dir.mkdir()
    
    report_file = report_dir / f'test_report_{timestamp}.txt'
    print(f"Running tests for WildOakDealsApp...")
    print(f"Generating report in {report_file}")
    
    exit_code = pytest.main(args)
    
    print("\nTest run complete.")
    print(f"Exit code: {exit_code}")
    
    if exit_code == 0:
        print("All tests passed! ✅")
    else:
        print("Some tests failed. ❌")
    
    return exit_code

if __name__ == '__main__':
    # Example usage:
    # create_test_file('new_feature', ['test_feature_works', 'test_feature_edge_case'])
    # run_tests('new_feature')
    run_tests()
