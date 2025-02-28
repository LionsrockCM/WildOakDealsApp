from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pathlib import Path
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask_sslify import SSLify
from functools import wraps
from flask_migrate import Migrate

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

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def role(self):
        return Role.query.get(self.role_id)

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user, remember=True)
            print(f"User {user.username} logged in as {user.role.name}")
            return redirect(url_for('home'))
        print("Login failed: Invalid username or password")
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    print("User logged out")
    return redirect(url_for('login'))

def check_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role.name == 'Admin' or (permission == 'view_own' and 'own' in permission):
                return f(*args, **kwargs)
            return jsonify({'error': 'Permission denied'}), 403
        return decorated_function
    return decorator

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
            if current_user.role.name != 'Admin' and not Deal.query.filter_by(user_id=current_user.id).first():
                return jsonify({'error': 'Permission denied'}), 403
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
            response = {
                'id': new_deal.id,
                'message': 'Deal added successfully',
                'created_at': new_deal.created_at.isoformat(),
                'updated_at': new_deal.created_at.isoformat()
            }
            return jsonify(response), 201
        except Exception as e:
            print(f"Error adding deal: {str(e)}")
            return jsonify({'error': str(e)}), 400
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
    return render_template('deal_detail.html', deal=deal, files=files)

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