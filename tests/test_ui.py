
import os
import sys
import pytest
from flask import url_for
from bs4 import BeautifulSoup

# Import helper functions from conftest
from conftest import login

def test_home_page_unauthenticated(client):
    """Test the home page redirects to login when unauthenticated."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_home_page_authenticated(client):
    """Test the home page loads correctly when authenticated."""
    login(client, 'testuser', 'testpassword')
    response = client.get('/')
    assert response.status_code == 200
    
    # Check for key elements on the home page
    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.find('a', class_='navbar-brand', string='Wild Oak Deals') is not None
    assert 'Add New Deal' in soup.get_text()
    assert 'Deal List' in soup.get_text()
    assert 'Deal Analytics' in soup.get_text()

def test_login_page(client):
    """Test the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data

def test_register_page(client):
    """Test the register page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'Sign Up' in response.data
