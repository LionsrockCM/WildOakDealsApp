from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pathlib import Path
from datetime import datetime
from flask_wtf.csrf import CSRFProtect, CSRFError
import smtplib
from email.mime.text import MIMEText
from flask_sslify import SSLify
from functools import wraps
from flask_migrate import Migrate
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# Ensure instance directory exists for SQLite database
instance_path = Path(app.instance_path)
instance_path.mkdir(exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{instance_path / "deals.db"}'
app.config['WTF_CSRF_ENABLED'] = True  # Enable CSRF protection
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

# Email configuration using Replit Secrets
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')

# Enable HTTPS redirection in production (optional, comment out for local testing)
if 'REPLIT_DEPLOYMENT' in os.environ:
    sslify = SSLify(app)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Increased length for hashed password
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, default=2)  # Default to User (role_id=2)
    email = db.Column(db.String(120), nullable=True)  # Optional email for notifications

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def role(self):
        return db.session.get(Role, self.role_id)  # Updated for SQLAlchemy 2.0 compatibility

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Simplified relationship - just one clean relationship with cascade delete
    status_histories = db.relationship('DealStatusHistory', backref='deal', cascade='all, delete-orphan')

class DealStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # The backref='deal' is now defined in the Deal class
    user = db.relationship('User', backref='status_changes')

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    dropbox_link = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def check_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role.name == 'Admin' or (permission == 'view_own' and 'own' in permission):
                return f(*args, **kwargs)
            if permission == 'admin_only' and current_user.role.name != 'Admin':
                return jsonify({'error': 'Permission denied'}), 403
            return jsonify({'error': 'Permission denied'}), 403
        return decorated_function
    return decorator

# Custom decorator to handle CSRF for API endpoints
def csrf_exempt(f):
    def decorated_function(*args, **kwargs):
        request.csrf_valid = True
        return f(*args, **kwargs)
    return decorated_function

def get_deal_analytics():
    if current_user.role.name == 'Admin':
        deals = Deal.query.all()
    else:
        deals = Deal.query.filter_by(user_id=current_user.id).all()

    # Analytics data
    status_counts = defaultdict(int)
    state_counts = defaultdict(int)
    user_counts = defaultdict(int)
    deals_by_month = defaultdict(int)

    for deal in deals:
        status_counts[deal.status] += 1
        state_counts[deal.state] += 1
        user_counts[deal.user_id] += 1
        deals_by_month[deal.created_at.strftime('%Y-%m')] += 1

    # Get user names for user_counts
    user_names = {user.id: user.username for user in User.query.all()}
    user_counts_formatted = {user_names[user_id]: count for user_id, count in user_counts.items()}

    return {
        'status_counts': dict(status_counts),
        'state_counts': dict(state_counts),
        'user_counts': user_counts_formatted,
        'deals_by_month': dict(deals_by_month)
    }

@app.route('/')
@login_required
def home():
    analytics = get_deal_analytics()
    return render_template('home.html', analytics=analytics)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Debug form data
            print("Form data:", request.form)
            print("CSRF token in session:", session.get('csrf_token'))
            print("CSRF token in form:", request.form.get('csrf_token'))
            
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                print("Login failed: Missing username or password")
                return render_template('login.html', error='Username and password are required')
                
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=True)
                print(f"User {user.username} logged in as {user.role.name}")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            
            print("Login failed: Invalid username or password")
            return render_template('login.html', error='Invalid username or password')
        except Exception as e:
            print(f"Login error: {str(e)}")
            return render_template('login.html', error='An error occurred during login')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', None)  # Optional email field
        if not username or not password:
            return render_template('register.html', error='Username and password are required')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            return render_template('register.html', error='Default User role not found')
        new_user = User(username=username, role_id=user_role.id, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        print(f"New user registered: {username} as User")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    print("User logged out")
    return redirect(url_for('login'))

@app.route('/api/users', methods=['POST', 'PUT'])
@login_required
@check_permission('admin_only')
@csrf_exempt  # Exempt CSRF for API endpoints (handled via header)
def manage_users():
    # Check for CSRF token in header if not exempted
    if not hasattr(request, 'csrf_valid') and not request.headers.get('X-CSRFToken') == csrf.generate_csrf():
        return jsonify({'error': 'CSRF token is missing or invalid'}), 400

    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            required_fields = ['username', 'password', 'role']
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                print(f"Missing fields for user creation: {missing}")
                return jsonify({'error': f'Missing required field: {missing[0]}'}), 400
            if User.query.filter_by(username=data.get('username')).first():
                return jsonify({'error': 'Username already exists'}), 400
            role = Role.query.filter_by(name=data.get('role')).first()
            if not role:
                return jsonify({'error': 'Invalid role'}), 400
            new_user = User(username=data.get('username'), role_id=role.id, email=data.get('email', None))
            new_user.set_password(data.get('password'))
            db.session.add(new_user)
            db.session.commit()
            print(f"New user created by Admin: {data.get('username')} as {role.name}")
            return jsonify({'message': 'User created successfully', 'username': new_user.username}), 201
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return jsonify({'error': str(e)}), 400

    if request.method == 'PUT':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            required_fields = ['username', 'role']
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                print(f"Missing fields for user update: {missing}")
                return jsonify({'error': f'Missing required field: {missing[0]}'}), 400
            user = User.query.filter_by(username=data.get('username')).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            role = Role.query.filter_by(name=data.get('role')).first()
            if not role:
                return jsonify({'error': 'Invalid role'}), 400
            user.role_id = role.id
            if 'password' in data:
                user.set_password(data.get('password'))
            if 'email' in data:
                user.email = data.get('email')
            db.session.commit()
            print(f"User updated by Admin: {data.get('username')} to role {role.name}")
            return jsonify({'message': 'User updated successfully', 'username': user.username}), 200
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return jsonify({'error': str(e)}), 400

@app.route('/api/deals', methods=['GET', 'POST'])
@login_required
@check_permission('view_own')
def deals():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            required_fields = ['deal_name', 'state', 'city', 'status']
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                print(f"Missing fields: {missing}")
                return jsonify({'error': f'Missing required field: {missing[0]}'}), 400
            # Allow Users to create deals even if they have no existing deals
            new_deal = Deal(
                deal_name=data.get('deal_name'),
                state=data.get('state'),
                city=data.get('city'),
                status=data.get('status'),
                user_id=current_user.id
            )
            db.session.add(new_deal)
            db.session.commit()
            print(f"Deal added: ID={new_deal.id}, Name={new_deal.deal_name}, User={current_user.username}")
            # Record initial status in history
            status_history = DealStatusHistory(deal_id=new_deal.id, status=new_deal.status, changed_by_user_id=current_user.id)
            db.session.add(status_history)
            db.session.commit()
            notify_status_change(new_deal, current_user)
            response = {
                'id': new_deal.id,
                'message': 'Deal added successfully',
                'created_at': new_deal.created_at.isoformat(),
                'updated_at': new_deal.updated_at.isoformat()
            }
            return jsonify(response), 201
        except Exception as e:
            print(f"Error adding deal: {str(e)}")
            return jsonify({'error': str(e)}), 400
    # Fetch all deals for Admin, only user's deals for User
    if current_user.role.name == 'Admin':
        deals = Deal.query.all()
        print(f"Fetched all {len(deals)} deals for Admin {current_user.id}")
    else:
        deals = Deal.query.filter_by(user_id=current_user.id).all()
        print(f"Fetched {len(deals)} deals for user {current_user.id}")
    return jsonify([{
        'id': d.id,
        'deal_name': d.deal_name,
        'state': d.state,
        'city': d.city,
        'status': d.status,
        'created_at': d.created_at.isoformat(),
        'updated_at': d.updated_at.isoformat()
    } for d in deals])

@app.route('/api/deals/<int:deal_id>', methods=['PUT', 'DELETE'])
@login_required
@check_permission('view_own')
def deal_modify(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if deal.user_id != current_user.id and current_user.role.name != 'Admin':
        return jsonify({'error': 'Permission denied'}), 403

    if request.method == 'PUT':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            required_fields = ['deal_name', 'state', 'city', 'status']
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                print(f"Missing fields for update: {missing}")
                return jsonify({'error': f'Missing required field: {missing[0]}'}), 400
            old_status = deal.status
            deal.deal_name = data.get('deal_name', deal.deal_name)
            deal.state = data.get('state', deal.state)
            deal.city = data.get('city', deal.city)
            deal.status = data.get('status', deal.status)
            deal.updated_at = datetime.utcnow()
            db.session.commit()
            if old_status != deal.status:
                status_history = DealStatusHistory(deal_id=deal_id, status=deal.status, changed_by_user_id=current_user.id)
                db.session.add(status_history)
                db.session.commit()
                notify_status_change(deal, current_user)
            print(f"Deal updated: ID={deal_id}, Name={deal.deal_name}, User={current_user.username}")
            return jsonify({
                'id': deal.id,
                'message': 'Deal updated successfully',
                'updated_at': deal.updated_at.isoformat()
            }), 200
        except Exception as e:
            print(f"Error updating deal: {str(e)}")
            return jsonify({'error': str(e)}), 400

    if request.method == 'DELETE':
        try:
            # Delete associated DealStatusHistory records first
            DealStatusHistory.query.filter_by(deal_id=deal_id).delete()
            db.session.delete(deal)
            db.session.commit()
            print(f"Deal deleted: ID={deal_id}, User={current_user.username}")
            return jsonify({'message': 'Deal deleted successfully'}), 200
        except Exception as e:
            print(f"Error deleting deal: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:deal_id>', methods=['GET', 'POST'])
@login_required
@check_permission('view_own')
def files(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if deal.user_id != current_user.id and current_user.role.name != 'Admin':
        return jsonify({'error': 'Permission denied'}), 403
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            required_fields = ['file_name', 'dropbox_link']
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                print(f"Missing fields: {missing}")
                return jsonify({'error': f'Missing required field: {missing[0]}'}), 400
            new_file = File(
                deal_id=deal_id,
                file_name=data.get('file_name'),
                dropbox_link=data.get('dropbox_link')
            )
            db.session.add(new_file)
            db.session.commit()
            print(f"File uploaded: ID={new_file.id}, Deal ID={deal_id}, User={current_user.username}")
            response = {
                'id': new_file.id,
                'message': 'File uploaded successfully'
            }
            return jsonify(response), 201
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return jsonify({'error': str(e)}), 400
    files = File.query.filter_by(deal_id=deal_id).all()
    print(f"Fetched {len(files)} files for deal {deal_id}")
    return jsonify([{
        'id': f.id,
        'deal_id': f.deal_id,
        'file_name': f.file_name,
        'dropbox_link': f.dropbox_link,
        'upload_date': f.upload_date.isoformat(),
        'created_at': f.created_at.isoformat(),
        'updated_at': f.updated_at.isoformat()
    } for f in files])

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
@check_permission('view_own')
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    deal = Deal.query.get_or_404(file.deal_id)
    if deal.user_id != current_user.id and current_user.role.name != 'Admin':
        return jsonify({'error': 'Permission denied'}), 403
    try:
        db.session.delete(file)
        db.session.commit()
        print(f"File deleted: ID={file_id}, Deal ID={file.deal_id}, User={current_user.username}")
        return jsonify({'message': 'File deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return jsonify({'error': 'Failed to delete file'}), 500

@app.route('/deal/<int:deal_id>')
@login_required
@check_permission('view_own')
def deal_detail(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    if deal.user_id != current_user.id and current_user.role.name != 'Admin':
        return jsonify({'error': 'Permission denied'}), 403
    files = File.query.filter_by(deal_id=deal_id).all()
    status_history = DealStatusHistory.query.filter_by(deal_id=deal_id).order_by(DealStatusHistory.changed_at.desc()).all()
    return render_template('deal_detail.html', deal=deal, files=files, status_history=status_history)

@app.route('/api/analytics', methods=['GET'])
@login_required
@check_permission('view_own')  # Allow Admins to see all, Users to see their own
def get_analytics():
    if current_user.role.name == 'Admin':
        deals = Deal.query.all()
    else:
        deals = Deal.query.filter_by(user_id=current_user.id).all()

    # Analytics data
    status_counts = defaultdict(int)
    state_counts = defaultdict(int)
    user_counts = defaultdict(int)
    deals_by_month = defaultdict(int)

    for deal in deals:
        status_counts[deal.status] += 1
        state_counts[deal.state] += 1
        user_counts[deal.user_id] += 1
        deals_by_month[deal.created_at.strftime('%Y-%m')] += 1

    # Get user names for user_counts
    user_names = {user.id: user.username for user in User.query.all()}
    user_counts_formatted = {user_names[user_id]: count for user_id, count in user_counts.items()}

    return jsonify({
        'status_counts': dict(status_counts),
        'state_counts': dict(state_counts),
        'user_counts': user_counts_formatted,
        'deals_by_month': dict(deals_by_month)
    })

# Handle CSRF errors globally for API endpoints
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({'error': 'CSRF token is missing or invalid'}), 400

def notify_status_change(deal, user):
    # Send email notification if user has an email
    if user.email:
        try:
            msg = MIMEText(f"Status change for deal '{deal.deal_name}' (ID: {deal.id}): {deal.status} by {user.username} at {datetime.utcnow()}")
            msg['Subject'] = f"Deal Status Update: {deal.deal_name}"
            msg['From'] = app.config['MAIL_USERNAME']
            msg['To'] = user.email

            with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
                server.starttls()
                server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                server.send_message(msg)
            print(f"Email notification sent to {user.email} for deal {deal.deal_name}")
        except Exception as e:
            print(f"Failed to send email notification: {str(e)}")
    else:
        # Fallback to console log if no email
        message = f"Status change for deal '{deal.deal_name}' (ID: {deal.id}): {deal.status} by {user.username} at {datetime.utcnow()}"
        print(message)

with app.app_context():
    try:
        db.create_all()
        # Initialize default roles if they don't exist
        if not Role.query.filter_by(name='Admin').first():
            admin_role = Role(name='Admin')
            db.session.add(admin_role)
        if not Role.query.filter_by(name='User').first():
            user_role = Role(name='User')
            db.session.commit()
        print("Database tables and roles created successfully")
    except Exception as e:
        print(f"Error creating database tables or roles: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True)