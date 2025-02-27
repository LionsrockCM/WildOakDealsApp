from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deals.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    dropbox_link = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user, remember=True)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/deals', methods=['GET', 'POST'])
@login_required
def deals():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            new_deal = Deal(
                deal_name=data.get('deal_name'),
                state=data.get('state'),
                city=data.get('city'),
                status=data.get('status'),
                user_id=current_user.id
            )
            db.session.add(new_deal)
            db.session.commit()
            response = {'id': new_deal.id, 'message': 'Deal added successfully'}
            return jsonify(response), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    deals = Deal.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': d.id,
        'deal_name': d.deal_name,
        'state': d.state,
        'city': d.city,
        'status': d.status
    } for d in deals])

@app.route('/api/files/<int:deal_id>', methods=['GET', 'POST'])
@login_required
def files(deal_id):
    if request.method == 'POST':
        data = request.json
        new_file = File(
            deal_id=deal_id,
            file_name=data.get('file_name'),
            dropbox_link=data.get('dropbox_link')
        )
        db.session.add(new_file)
        db.session.commit()
        return jsonify({'id': new_file.id}), 201
    files = File.query.filter_by(deal_id=deal_id).all()
    return jsonify([{
        'id': f.id,
        'deal_id': f.deal_id,
        'file_name': f.file_name,
        'dropbox_link': f.dropbox_link,
        'upload_date': f.upload_date.isoformat()
    } for f in files])

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)), debug=True)