
import os
import sys
import pytest

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

@pytest.fixture
def authenticated_client(client):
    """Create a test client that's already logged in."""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    return client

@pytest.fixture
def test_deal(client):
    """Create a test deal in the database."""
    login(client, 'testuser', 'testpassword')
    
    with app.app_context():
        test_user = User.query.filter_by(username='testuser').first()
        test_deal = Deal(
            deal_name='Test Deal',
            state='California',
            city='Los Angeles',
            status='Pending',
            user_id=test_user.id
        )
        db.session.add(test_deal)
        db.session.commit()
        return test_deal.id

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)
