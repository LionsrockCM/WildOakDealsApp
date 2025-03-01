from main import app, db, User
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"Username: {user.username}, Email: {user.email}, Role: {user.role.name}")