from main import app, db, User
with app.app_context():
    user = User.query.filter_by(username='test').first()
    if user:
        user.email = 'dpledoux@gmail.com'
        db.session.commit()
    user = User.query.filter_by(username='admin').first()
    if user:
        user.email = 'dpledoux@gmail.com'
        db.session.commit()