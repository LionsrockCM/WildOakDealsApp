
"""
Utility functions for testing WildOakDealsApp.
"""
import os
import sys
import datetime
import subprocess

def run_tests(pattern=None, verbose=True):
    """Run tests and generate a report."""
    # Create test reports directory if it doesn't exist
    if not os.path.exists('test_reports'):
        os.makedirs('test_reports')
    
    # Generate timestamp for the report file name
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f'test_reports/test_report_{timestamp}.txt'
    
    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest"]
    if verbose:
        pytest_cmd.append("-v")
    if pattern:
        pytest_cmd.append(pattern)
    
    # Capture output to file
    with open(report_file, 'w') as f:
        try:
            process = subprocess.run(pytest_cmd, capture_output=True, text=True)
            f.write(process.stdout)
            f.write(process.stderr)
            f.write(f"\nTest run complete.\nExit code: {process.returncode}\n")
            
            if process.returncode == 0:
                f.write("All tests passed! ✅\n")
            else:
                f.write("Some tests failed. ❌\n")
                
            return process.returncode
            
        except Exception as e:
            error_msg = f"Error running tests: {str(e)}"
            f.write(error_msg + "\n")
            print(error_msg)
            return 1

def create_test_file(component, test_type="ui"):
    """
    Create a new test file for a component.
    
    Args:
        component (str): Name of the component to test
        test_type (str): Type of test - ui, api, etc.
    
    Returns:
        str: Path to the created test file
    """
    test_file = f"tests/test_{component}_{test_type}.py"
    
    # Create tests directory if it doesn't exist
    if not os.path.exists('tests'):
        os.makedirs('tests')
        # Create __init__.py in tests directory
        with open('tests/__init__.py', 'w') as f:
            f.write('# Tests package\n')
    
    # Don't overwrite existing files
    if os.path.exists(test_file):
        print(f"Test file {test_file} already exists, skipping creation.")
        return test_file
    
    # Create basic test template
    with open(test_file, 'w') as f:
        f.write(f"""import os
import sys
import pytest
from bs4 import BeautifulSoup

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role

@pytest.fixture
def client():
    \"\"\"Create a test client for the app.\"\"\"
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
    \"\"\"Helper function to log in a user.\"\"\"
    return client.post('/login', data={{
        'username': username,
        'password': password
    }}, follow_redirects=True)

def test_{component}_basic():
    \"\"\"Basic test for {component}.\"\"\"
    assert True
""")
    
    print(f"Created test file: {test_file}")
    return test_file
