import os
import sys
import pytest
from flask import url_for
from bs4 import BeautifulSoup
from main import app, db, Deal, File, DealStatusHistory

# Import helper functions from conftest
from conftest import login

def test_deal_detail_page(client, test_deal):
    """Test the deal detail page loads correctly."""
    login(client, 'testuser', 'testpassword')
    response = client.get(f'/deal/{test_deal}')
    assert response.status_code == 200

    # Check that the page contains the deal name
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Test Deal' in soup.get_text()

    # Check that edit and delete buttons are present
    assert soup.find('button', string='Edit Deal') is not None
    assert soup.find('button', string='Delete Deal') is not None

    # Check that the file upload form is present
    assert soup.find('form', id='fileForm') is not None

def test_deal_edit(client, test_deal):
    """Test editing a deal."""
    login(client, 'testuser', 'testpassword')
    response = client.put(f'/api/deals/{test_deal}', data={
        'deal_name': 'Updated Test Deal',
        'state': 'Texas',
        'city': 'Austin',
        'status': 'Active'
    })
    assert response.status_code == 200

    # Verify the deal was updated
    with app.app_context():
        deal = Deal.query.get(test_deal)
        assert deal.deal_name == 'Updated Test Deal'
        assert deal.state == 'Texas'
        assert deal.city == 'Austin'
        assert deal.status == 'Active'