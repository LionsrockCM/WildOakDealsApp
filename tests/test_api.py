import os
import sys
import pytest
import json
from flask import url_for
from main import app, db, User, Role, Deal

# Import the login function from conftest
from conftest import login

def test_api_deals_get(client):
    """Test fetching deals via API."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/api/deals')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_api_deals_post(client):
    """Test creating a new deal."""
    login(client, 'testuser', 'testpassword')
    response = client.post('/api/deals', data={
        'deal_name': 'Test API Deal',
        'state': 'California',
        'city': 'Los Angeles',
        'status': 'Pending'
    })
    assert response.status_code in [200, 201]
    data = json.loads(response.data)
    assert 'message' in data
    assert 'id' in data

    # Verify the deal was created
    with app.app_context():
        deal = Deal.query.filter_by(deal_name='Test API Deal').first()
        assert deal is not None
        assert deal.state == 'California'
        assert deal.city == 'Los Angeles'
        assert deal.status == 'Pending'

def test_api_analytics(client):
    """Test analytics endpoint."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/api/analytics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status_counts' in data
    assert 'state_counts' in data
    assert 'user_counts' in data
    assert 'deals_by_month' in data