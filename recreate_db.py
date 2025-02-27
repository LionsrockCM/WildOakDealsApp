from main import app, db, User  # Added User import
from sqlalchemy.sql import text
import json
from datetime import datetime

with app.app_context():
    # Backup existing users
    users = db.session.execute(text("SELECT id, username, password FROM user")).fetchall()
    user_backup = [{"id": user[0], "username": user[1], "password": user[2]} for user in users]
    with open("user_backup.json", "w") as f:
        json.dump(user_backup, f)

    # Recreate database
    db.drop_all()
    db.create_all()
    print("Database recreated successfully!")

    # Restore users
    with open("user_backup.json", "r") as f:
        user_backup = json.load(f)
    for user_data in user_backup:
        new_user = User(id=user_data["id"], username=user_data["username"], password=user_data["password"])
        db.session.add(new_user)
    db.session.commit()
    print("Users restored successfully!")