
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
    """Test that the register page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Register' in soup.find('title').text
    assert soup.find('form') is not None
    assert soup.find('input', {'name': 'username'}) is not None
    assert soup.find('input', {'name': 'password'}) is not None
    assert soup.find('input', {'name': 'confirm_password'}) is not None
    assert soup.find('button', {'type': 'submit'}) is not None

def test_register_ui_elements(client):
    """Test that the register page has the correct UI elements."""
    response = client.get('/register')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check navbar
    navbar = soup.find('div', {'class': 'navbar'})
    assert navbar is not None
    assert navbar.find('a', {'class': 'navbar-brand'}) is not None
    
    # Check form controls
    form = soup.find('form')
    assert form is not None
    assert form.find('input', {'name': 'csrf_token'}) is not None
    assert form.find('input', {'id': 'username'}) is not None
    assert form.find('input', {'id': 'password'}) is not None
    assert form.find('input', {'id': 'confirm_password'}) is not None
    assert form.find('button', {'type': 'submit'}) is not None
    
    # Check login link
    login_link = soup.find('a', href='/login')
    assert login_link is not None

def test_register_submission(client):
    """Test that a user can register successfully."""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'password123',
        'confirm_password': 'password123',
        'email': 'newuser@example.com'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Check that we've been redirected to login page
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Login' in soup.find('title').text
    
    # Verify user was created in database
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
