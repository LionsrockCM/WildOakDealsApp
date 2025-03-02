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
    assert soup.title.string == 'Register - Wild Oak Deals'

    # Check for the registration form
    form = soup.find('form', {'method': 'POST'})
    assert form is not None

    # Check for username and password fields
    assert form.find('input', {'id': 'username'}) is not None
    assert form.find('input', {'id': 'password'}) is not None

def test_user_registration(client):
    """Test that a user can register."""
    # Register a new user
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpassword',
        'email': 'newuser@example.com'
    }, follow_redirects=True)

    assert response.status_code == 200

    # Verify user was created
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        # Check that user has the User role, not Admin
        role = Role.query.get(user.role_id)
        assert role.name == 'User'