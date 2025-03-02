import os
import sys
import pytest
from flask import url_for

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

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_api_login_required(client):
    """Test that API endpoints require login."""
    response = client.get('/api/deals')
    assert response.status_code == 401 or response.status_code == 302

def test_api_deals_get(client):
    """Test getting deals after login."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/api/deals')
    assert response.status_code == 200
    assert b'[]' in response.data  # Empty list since no deals created yet

def test_api_deals_post(client):
    """Test creating a new deal."""
    login(client, 'testuser', 'testpassword')
    response = client.post('/api/deals', data={
        'deal_name': 'Test Deal',
        'state': 'California',
        'city': 'Los Angeles',
        'status': 'Pending'
    })
    assert response.status_code == 201
    assert b'Deal added successfully' in response.data

def test_api_analytics(client):
    """Test analytics endpoint."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/api/analytics')
    assert response.status_code == 200
    assert b'status_counts' in response.data
    assert b'state_counts' in response.data