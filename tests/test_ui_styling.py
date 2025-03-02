
import pytest
from bs4 import BeautifulSoup
from conftest import login

def test_login_page_styling(client):
    """Test that the login page has the Wild Oak styling."""
    response = client.get('/login')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for navbar with Wild Oak branding
    navbar = soup.find('div', class_='navbar')
    assert navbar is not None
    assert navbar.find('a', class_='navbar-brand', string='Wild Oak Deals') is not None
    
    # Check for card-based layout
    card = soup.find('div', class_='card')
    assert card is not None
    assert card.find('div', class_='card-header') is not None
    assert card.find('div', class_='card-body') is not None
    
    # Check for form styling
    form = soup.find('form')
    assert form is not None
    assert form.find('input', class_='form-control') is not None
    assert form.find('button', class_='btn btn-primary') is not None

def test_deal_detail_styling(client, test_deal):
    """Test that the deal detail page has the Wild Oak styling."""
    login(client, 'testuser', 'testpassword')
    response = client.get(f'/deal/{test_deal}')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for navbar
    navbar = soup.find('div', class_='navbar')
    assert navbar is not None
    
    # Check for card-based layout
    cards = soup.find_all('div', class_='card')
    assert len(cards) >= 3  # Should have deal details, files section, and upload form
    
    # Check for status badges
    status_badge = soup.find('span', class_='status-badge')
    assert status_badge is not None
    
    # Check for action buttons styling
    action_buttons = soup.find('div', class_='action-buttons')
    assert action_buttons is not None
    assert action_buttons.find('button', class_='btn btn-primary') is not None
    
    # Check for form styling in file upload
    form = soup.find('form', id='fileForm')
    assert form is not None
    assert form.find('input', class_='form-control') is not None
