import os
import sys
import pytest
from bs4 import BeautifulSoup

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role, Deal
from tests.conftest import login

def test_deal_detail_page_requires_login(client):
    """Test that deal detail page requires login."""
    response = client.get('/deal/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_deal_detail_page_loads(client, test_deal):
    """Test that deal detail page loads correctly."""
    # Login first
    login(client, 'testuser', 'testpassword')

    # Access the deal page
    response = client.get(f'/deal/{test_deal.id}')
    assert response.status_code == 200

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')

    # Check for deal detail elements
    assert soup.find('h1', string='Deal Details') is not None
    assert soup.find('button', string='Edit Deal') is not None
    assert soup.find('button', string='Delete Deal') is not None
    assert soup.find('h2', string='Associated Files') is not None
    assert soup.find('h2', string='Upload New File') is not None


def test_deal_detail_requires_login(client):
    """Test that deal detail page requires login."""
    with app.app_context():
        deal = Deal.query.first()
        if deal:
            response = client.get(f'/deal/{deal.id}')
            assert response.status_code == 302  # Redirect to login

def test_deal_detail_page_loads_original(client):
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