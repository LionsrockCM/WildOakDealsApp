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
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_login_page_loads(client):
    """Test that login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data

def test_login_form_submission(client):
    """Test login form submission."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_home_page_requires_login(client):
    """Test that home page requires login."""
    response = client.get('/')
    assert response.status_code == 302  # Redirect to login

def test_home_page_after_login(client):
    """Test home page after login."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data
    assert b'Deal List' in response.data

    # Parse the HTML to check for specific elements
    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.title is not None
    assert 'Real Estate Deal Manager' in soup.title.text

    # Check for form elements
    forms = soup.find_all('form')
    assert len(forms) >= 1

    # Check for table
    tables = soup.find_all('table')
    assert len(tables) >= 1