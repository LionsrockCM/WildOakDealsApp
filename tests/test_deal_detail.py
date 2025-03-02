import os
import sys
import pytest
from bs4 import BeautifulSoup

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

            # Create test user
            test_user = User(username='testuser', role_id=user_role.id)
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()

            # Create test deal
            test_deal = Deal(
                deal_name="Test Deal",
                state="CA",
                city="Test City",
                status="Pending",
                user_id=test_user.id
            )
            db.session.add(test_deal)
            db.session.commit()

            # Create test status history
            status_history = DealStatusHistory(
                deal_id=test_deal.id,
                status="Pending",
                changed_by_user_id=test_user.id
            )
            db.session.add(status_history)
            db.session.commit()

            # Create test file
            test_file = File(
                deal_id=test_deal.id,
                file_name="Test File",
                dropbox_link="https://dropbox.com/test"
            )
            db.session.add(test_file)
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
    assert 'CA' in state.text
    
    city = soup.find('p', string=lambda text: 'City:' in text if text else False)
    assert city is not None
    assert 'Test City' in city.text
    
    status = soup.find('p', string=lambda text: 'Status:' in text if text else False)
    assert status is not None
    assert 'Pending' in status.text
    
    # Check for status history
    status_history_header = soup.find('h2', string='Status History')
    assert status_history_header is not None
    
    status_history_items = soup.find('ul', id=None)  # Status history doesn't have an ID
    assert status_history_items is not None
    
    # Check for file list
    file_list_header = soup.find('h2', string='Associated Files')
    assert file_list_header is not None
    
    file_list = soup.find('ul', id='fileList')
    assert file_list is not None
    assert 'Test File' in file_list.text
    assert 'View on Dropbox' in file_list.text
    
    # Check for file upload form
    file_upload_header = soup.find('h2', string='Upload New File')
    assert file_upload_header is not None
    
    file_upload_form = soup.find('form', id='fileForm')
    assert file_upload_form is not None
    
    file_name_field = file_upload_form.find('input', {'id': 'file_name'})
    assert file_name_field is not None
    
    dropbox_link_field = file_upload_form.find('input', {'id': 'dropbox_link'})
    assert dropbox_link_field is not None
    
    upload_button = file_upload_form.find('button', type='submit')
    assert upload_button is not None
    assert 'Upload File' in upload_button.text

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

        # Verify status history was created
        status_history = DealStatusHistory.query.filter_by(deal_id=deal_id, status='Active').first()
        assert status_history is not None