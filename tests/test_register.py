
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

def test_register_page_ui(client):
    """Test that the register page has the correct UI elements."""
    # We need to update the register.html page first to match our new UI
    # For now, we'll just test the basic functionality
    response = client.get('/register')
    assert response.status_code == 200
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Test basic elements
    form = soup.find('form')
    assert form is not None
    
    # Check for CSRF token
    csrf_token = form.find('input', {'name': 'csrf_token'})
    assert csrf_token is not None
    
    # Check for username field
    username_field = form.find('input', {'name': 'username'})
    assert username_field is not None
    
    # Check for password field
    password_field = form.find('input', {'name': 'password'})
    assert password_field is not None
    assert password_field['type'] == 'password'
    
    # Check for email field
    email_field = form.find('input', {'name': 'email'})
    assert email_field is not None
    
    # Check for register button
    register_button = form.find('button', type='submit')
    assert register_button is not None
    assert register_button.text == 'Register'

def test_register_functionality(client):
    """Test that the registration functionality works correctly."""
    # Register a new user
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpassword',
        'email': 'newuser@example.com'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Check that we're redirected to login page
    assert b'Login' in response.data
    
    # Verify user was created
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('newpassword')
        assert user.email == 'newuser@example.com'
        assert user.role_id == Role.query.filter_by(name='User').first().id

def test_register_duplicate_username(client):
    """Test that registration fails with a duplicate username."""
    # Create a user first
    client.post('/register', data={
        'username': 'existinguser',
        'password': 'password',
        'email': 'existing@example.com'
    })
    
    # Try to register with the same username
    response = client.post('/register', data={
        'username': 'existinguser',
        'password': 'newpassword',
        'email': 'new@example.com'
    })
    
    assert response.status_code == 200
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for error message
    error = soup.find('p', style='color: red;')
    assert error is not None
    assert 'Username already exists' in error.text
