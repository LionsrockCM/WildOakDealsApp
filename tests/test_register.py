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

        yield client

        with app.app_context():
            db.drop_all()

def test_register_page_loads(client):
    """Test that registration page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

    # Parse HTML to verify UI elements
    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.find('input', {'name': 'username'}) is not None
    assert soup.find('input', {'name': 'password'}) is not None
    assert soup.find('button', {'type': 'submit'}) is not None

def test_register_new_user(client):
    """Test registration of a new user."""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'password123',
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Check that we're redirected to login page
    assert b'Login' in response.data

    # Verify user was created
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.username == 'newuser'

def test_register_existing_username(client):
    """Test registration with an existing username."""
    # First create a user
    client.post('/register', data={
        'username': 'existinguser',
        'password': 'password123'
    })

    # Try to register again with the same username
    response = client.post('/register', data={
        'username': 'existinguser',
        'password': 'newpassword'
    })
    assert response.status_code == 200
    assert b'Username already exists' in response.data