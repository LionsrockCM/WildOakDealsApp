
from main import app, db, User

with app.app_context():
    # Check if user already exists
    existing_user = User.query.filter_by(username='test').first()
    if existing_user:
        print("User 'test' already exists in the database.")
    else:
        # Create new user
        new_user = User(username='test', password='test')
        db.session.add(new_user)
        db.session.commit()
        print("User 'test' has been added successfully.")
