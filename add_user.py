from main import app, db, User

with app.app_context():
    user = User.query.filter_by(username='test').first()
    if not user:
        user = User(username='test')
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    print("User 'test' added/updated with hashed password")