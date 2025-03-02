import os
import sys
import pytest
from bs4 import BeautifulSoup

# Add parent directory to path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, db, User, Role
from tests.conftest import login

def test_home_page_requires_login(client):
    """Test that home page requires login."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_home_page_after_login(client):
    """Test that home page loads correctly after login."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/')
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.find('h1', string='Welcome to Real Estate Deal Manager') is not None
    assert soup.find('h2', string='Add New Deal') is not None
    assert soup.find('h2', string='Deal List') is not None
    assert soup.find('h2', string='Deal Analytics') is not None

    # Check for form elements
    assert soup.find('form', {'id': 'dealForm'}) is not None
    assert soup.find('input', {'id': 'deal_name'}) is not None
    assert soup.find('input', {'id': 'state'}) is not None
    assert soup.find('input', {'id': 'city'}) is not None
    assert soup.find('input', {'id': 'status'}) is not None

    # Check for table
    assert soup.find('table', {'id': 'dealTable'}) is not None

    # Check for charts
    assert soup.find('canvas', {'id': 'statusChart'}) is not None
    assert soup.find('canvas', {'id': 'stateChart'}) is not None
    assert soup.find('canvas', {'id': 'userChart'}) is not None
    assert soup.find('canvas', {'id': 'monthChart'}) is not None

    # Check for logout link
    assert soup.find('a', string='Logout') is not None