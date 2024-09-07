from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create a new admin user
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('your_secure_password')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully.")