import os
import sys
import pytest
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

            # Create test deal
            test_deal = Deal(
                deal_name='Test Deal',
                state='California',
                city='Los Angeles',
                status='Pending',
                user_id=test_user.id
            )
            db.session.add(test_deal)
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

def test_deal_detail_requires_login(client):
    """Test that deal detail page requires login."""
    with app.app_context():
        deal = Deal.query.first()
        if deal:
            response = client.get(f'/deal/{deal.id}')
            assert response.status_code == 302  # Redirect to login

def test_deal_detail_page_loads(client):
    """Test that deal detail page loads correctly after login."""
    login(client, 'testuser', 'testpassword')

    with app.app_context():
        deal = Deal.query.first()
        if deal:
            response = client.get(f'/deal/{deal.id}')
            assert response.status_code == 200
            assert bytes(deal.deal_name, 'utf-8') in response.data

            # Parse HTML to verify UI elements
            soup = BeautifulSoup(response.data, 'html.parser')
            assert soup.find('h1', text='Deal Details') is not None
            assert soup.find('button', text='Edit Deal') is not None
            assert soup.find('button', text='Delete Deal') is not None

def test_deal_detail_page(client):
    """Test that the deal detail page displays the correct information."""
    # Login as test user
    login(client, 'testuser', 'testpassword')

    # Get deal ID
    with app.app_context():
        deal_id = Deal.query.filter_by(deal_name="Test Deal").first().id

    # Get deal detail page
    response = client.get(f'/deal/{deal_id}')
    assert response.status_code == 200

    # Parse response
    soup = BeautifulSoup(response.data, 'html.parser')

    # Check that deal name is displayed
    deal_name = soup.find('h2')
    assert deal_name is not None
    assert 'Test Deal' in deal_name.text

    # Check that deal details are displayed
    state = soup.find('p', string=lambda text: 'State:' in text if text else False)
    assert state is not None
    assert 'California' in state.text

    city = soup.find('p', string=lambda text: 'City:' in text if text else False)
    assert city is not None
    assert 'Los Angeles' in city.text

    status = soup.find('p', string=lambda text: 'Status:' in text if text else False)
    assert status is not None
    assert 'Pending' in status.text


def test_edit_deal_functionality(client):
    """Test that a user can edit their own deal."""
    # Login as test user
    login(client, 'testuser', 'testpassword')

    # Get deal ID
    with app.app_context():
        deal_id = Deal.query.filter_by(deal_name="Test Deal").first().id

    # Update deal
    response = client.put(f'/api/deals/{deal_id}', data={
        'deal_name': 'Updated Test Deal',
        'state': 'NY',
        'city': 'New City',
        'status': 'Active'
    })

    assert response.status_code == 200

    # Verify deal was updated
    with app.app_context():
        deal = Deal.query.get(deal_id)
        assert deal is not None
        assert deal.deal_name == 'Updated Test Deal'
        assert deal.state == 'NY'
        assert deal.city == 'New City'
        assert deal.status == 'Active'