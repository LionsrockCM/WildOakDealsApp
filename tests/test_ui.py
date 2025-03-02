import os
import sys
import pytest
import time
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

def test_login_ui_elements(client):
    """Test that the login page has the correct UI elements."""
    response = client.get('/login')
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, 'html.parser')

    # Check for brand colors in CSS
    style_link = soup.find('link', {'rel': 'stylesheet'})
    assert style_link is not None
    assert 'styles.css' in style_link['href']

    # Check for navbar
    navbar = soup.find('div', {'class': 'navbar'})
    assert navbar is not None

    # Check for login form elements
    form = soup.find('form', {'method': 'POST'})
    assert form is not None

    # Check for username and password inputs
    username_input = form.find('input', {'id': 'username'})
    assert username_input is not None
    password_input = form.find('input', {'id': 'password'})
    assert password_input is not None

    # Check for login button
    login_button = form.find('button', {'type': 'submit'})
    assert login_button is not None
    assert 'Login' in login_button.text

    # Check for register link
    register_link = soup.find('a', href='/register')
    assert register_link is not None
    assert 'Register' in register_link.text

def test_home_page_ui_after_login(client):
    """Test that the home page has the correct UI elements after login."""
    # Login
    login(client, 'testuser', 'testpassword')

    # Get home page
    response = client.get('/')
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, 'html.parser')

    # Check for welcome message
    welcome_msg = soup.find('p', string=lambda text: 'Welcome, testuser' in text if text else False)
    assert welcome_msg is not None

    # Check for deal form
    deal_form = soup.find('form', {'id': 'dealForm'})
    assert deal_form is not None

    # Check for analytics section
    analytics = soup.find('h2', string='Deal Analytics')
    assert analytics is not None

    # Check for charts
    status_chart = soup.find('canvas', {'id': 'statusChart'})
    assert status_chart is not None
    state_chart = soup.find('canvas', {'id': 'stateChart'})
    assert state_chart is not None
    user_chart = soup.find('canvas', {'id': 'userChart'})
    assert user_chart is not None
    month_chart = soup.find('canvas', {'id': 'monthChart'})
    assert month_chart is not None