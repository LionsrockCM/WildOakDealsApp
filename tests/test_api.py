import os
import sys
import pytest
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role, Deal, DealStatusHistory, File

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

            # Create test users
            test_user = User(username='testuser', role_id=user_role.id)
            test_user.set_password('testpassword')

            admin_user = User(username='adminuser', role_id=admin_role.id)
            admin_user.set_password('adminpassword')

            db.session.add(test_user)
            db.session.add(admin_user)
            db.session.commit()

            # Create test deals
            test_deal = Deal(
                deal_name="Test Deal",
                state="CA",
                city="Test City",
                status="Pending",
                user_id=test_user.id
            )
            admin_deal = Deal(
                deal_name="Admin Deal",
                state="NY",
                city="Admin City",
                status="Active",
                user_id=admin_user.id
            )
            db.session.add(test_deal)
            db.session.add(admin_deal)
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

def test_get_deals_api(client):
    """Test that users can access the deals API."""
    # Login
    login(client, 'testuser', 'testpassword')

    # Get deals
    response = client.get('/api/deals')
    assert response.status_code == 200

    # Verify response contains the test deal
    data = response.get_json()
    assert any(deal['deal_name'] == 'Test Deal' for deal in data)
    assert not any(deal['deal_name'] == 'Admin Deal' for deal in data)

def test_api_deals_admin_get(client):
    """Test that the deals API returns all deals for an admin."""
    # Login as admin user
    login(client, 'adminuser', 'adminpassword')
    
    # Get deals
    response = client.get('/api/deals')
    assert response.status_code == 200
    
    # Parse response
    deals = json.loads(response.data)
    assert len(deals) == 2
    
    # Find deals by name
    test_deal = next((d for d in deals if d['deal_name'] == "Test Deal"), None)
    admin_deal = next((d for d in deals if d['deal_name'] == "Admin Deal"), None)
    
    assert test_deal is not None
    assert admin_deal is not None
    assert test_deal['state'] == "CA"
    assert admin_deal['state'] == "NY"

def test_api_deals_post(client):
    """Test that a user can create a new deal."""
    # Login as test user
    login(client, 'testuser', 'testpassword')
    
    # Create new deal
    response = client.post('/api/deals', data={
        'deal_name': "New Test Deal",
        'state': "TX",
        'city': "New Test City",
        'status': "Active"
    })
    
    assert response.status_code == 201
    
    # Verify deal was created
    with app.app_context():
        deal = Deal.query.filter_by(deal_name="New Test Deal").first()
        assert deal is not None
        assert deal.state == "TX"
        assert deal.city == "New Test City"
        assert deal.status == "Active"
        assert deal.user_id == User.query.filter_by(username='testuser').first().id
        
        # Verify status history was created
        status_history = DealStatusHistory.query.filter_by(deal_id=deal.id).first()
        assert status_history is not None
        assert status_history.status == "Active"

def test_api_files_get(client):
    """Test that a user can get files for a deal."""
    # Login as test user
    login(client, 'testuser', 'testpassword')
    
    # Get test deal ID
    with app.app_context():
        deal_id = Deal.query.filter_by(deal_name="Test Deal").first().id
    
    # Get files
    response = client.get(f'/api/files/{deal_id}')
    assert response.status_code == 200
    
    # Parse response
    files = json.loads(response.data)
    assert len(files) == 1
    assert files[0]['file_name'] == "Test File"
    assert files[0]['dropbox_link'] == "https://dropbox.com/testlink"

def test_api_files_post(client):
    """Test that a user can create a new file for a deal."""
    # Login as test user
    login(client, 'testuser', 'testpassword')
    
    # Get test deal ID
    with app.app_context():
        deal_id = Deal.query.filter_by(deal_name="Test Deal").first().id
    
    # Create new file
    response = client.post(f'/api/files/{deal_id}', data={
        'file_name': "New Test File",
        'dropbox_link': "https://dropbox.com/newlink"
    })
    
    assert response.status_code == 201
    
    # Verify file was created
    with app.app_context():
        file = File.query.filter_by(file_name="New Test File").first()
        assert file is not None
        assert file.dropbox_link == "https://dropbox.com/newlink"
        assert file.deal_id == deal_id

def test_api_analytics(client):
    """Test that the analytics API returns the correct data."""
    # Login as admin user to see all analytics
    login(client, 'adminuser', 'adminpassword')
    
    # Get analytics
    response = client.get('/api/analytics')
    assert response.status_code == 200
    
    # Parse response
    analytics = json.loads(response.data)
    assert 'status_counts' in analytics
    assert 'state_counts' in analytics
    assert 'user_counts' in analytics
    assert 'deals_by_month' in analytics
    
    # Check status counts
    assert analytics['status_counts']['Pending'] == 1
    assert analytics['status_counts']['Active'] == 1
    
    # Check state counts
    assert analytics['state_counts']['CA'] == 1
    assert analytics['state_counts']['NY'] == 1
    
    # Check user counts (should use usernames)
    assert 'testuser' in analytics['user_counts']
    assert 'adminuser' in analytics['user_counts']
    assert analytics['user_counts']['testuser'] == 1
    assert analytics['user_counts']['adminuser'] == 1
    
    # Check deals by month
    # Get current month
    current_month = datetime.utcnow().strftime('%Y-%m')
    assert current_month in analytics['deals_by_month']
    assert analytics['deals_by_month'][current_month] == 2  # 2 deals created this month