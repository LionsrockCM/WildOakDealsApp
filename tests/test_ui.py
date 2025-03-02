
import os
import sys
import pytest
from flask import url_for
from bs4 import BeautifulSoup

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role, Deal

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

def test_login_page_ui(client):
    """Test that the login page has the correct UI elements."""
    response = client.get('/login')
    assert response.status_code == 200
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Test navbar
    navbar = soup.find('div', class_='navbar')
    assert navbar is not None
    brand = navbar.find('a', class_='navbar-brand')
    assert brand is not None
    assert brand.text == 'Wild Oak Deals'
    
    # Test form elements
    card = soup.find('div', class_='card')
    assert card is not None
    
    card_header = card.find('div', class_='card-header')
    assert card_header is not None
    assert card_header.find('h2').text == 'Login'
    
    form = card.find('form')
    assert form is not None
    
    # Check for CSRF token
    csrf_token = form.find('input', {'name': 'csrf_token'})
    assert csrf_token is not None
    
    # Check for username field
    username_field = form.find('input', {'id': 'username'})
    assert username_field is not None
    assert username_field['required'] is not None
    
    # Check for password field
    password_field = form.find('input', {'id': 'password'})
    assert password_field is not None
    assert password_field['type'] == 'password'
    assert password_field['required'] is not None
    
    # Check for login button
    login_button = form.find('button', type='submit')
    assert login_button is not None
    assert login_button.text == 'Login'
    
    # Check for register link
    register_link = card.find('a', href='/register')
    assert register_link is not None
    assert 'Register' in register_link.text

def test_login_functionality(client):
    """Test that the login functionality works correctly."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome, testuser!' in response.data

def test_login_invalid_credentials(client):
    """Test that login fails with invalid credentials."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 200
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for error message
    error = soup.find('div', class_='alert-error')
    assert error is not None
    assert 'Invalid username or password' in error.text

def test_login_page_css(client):
    """Test that the CSS is correctly applied to the login page."""
    response = client.get('/login')
    assert response.status_code == 200
    
    # Check for CSS link
    soup = BeautifulSoup(response.data, 'html.parser')
    css_link = soup.find('link', rel='stylesheet')
    assert css_link is not None
    assert 'styles.css' in css_link['href']
    
    # Get the CSS file
    css_url = css_link['href']
    css_response = client.get(css_url)
    assert css_response.status_code == 200
    
    # Check for brand colors in CSS
    css_content = css_response.data.decode('utf-8')
    assert '--color-white: #FFFFFF;' in css_content
    assert '--color-dark-gray: #333333;' in css_content
    assert '--color-gold: #FFD700;' in css_content
