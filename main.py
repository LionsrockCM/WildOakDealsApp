
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
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        if user and user.password == request.form['password']:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/api/deals', methods=['GET', 'POST'])
@login_required
def deals():
    if request.method == 'POST':
        data = request.json
        new_deal = Deal(
            name=data['name'],
            address=data['address'],
            price=data['price'],
            units=data['units'],
            user_id=current_user.id
        )
        db.session.add(new_deal)
        db.session.commit()
        return jsonify({'id': new_deal.id}), 201
    
    deals = Deal.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'address': d.address,
        'price': d.price,
        'units': d.units
    } for d in deals])

@app.route('/api/files/<int:deal_id>', methods=['GET', 'POST'])
@login_required
def files(deal_id):
    if request.method == 'POST':
        file = request.files['file']
        new_file = File(filename=file.filename, deal_id=deal_id)
        db.session.add(new_file)
        db.session.commit()
        return jsonify({'id': new_file.id}), 201
    
    files = File.query.filter_by(deal_id=deal_id).all()
    return jsonify([{
        'id': f.id,
        'filename': f.filename,
        'uploaded_at': f.uploaded_at
    } for f in files])

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
