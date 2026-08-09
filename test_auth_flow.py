from app import app
from models import db, User

client = app.test_client()

with app.app_context():
    # Clean up if exists
    u = User.query.filter_by(phone='01234567890').first()
    if u:
        db.session.delete(u)
        db.session.commit()

# Test Register
response = client.post('/register', data={
    'name': 'Real Student',
    'phone': '01234567890',
    'password': 'password123',
    'confirm_password': 'password123'
}, follow_redirects=True)

print("Register status code:", response.status_code)
print("Register response length:", len(response.data))

# Verify DB
with app.app_context():
    u = User.query.filter_by(phone='01234567890').first()
    print("User role in DB:", u.role if u else "Not Found")
    print("User password hash starts with:", u.password_hash[:10] if u else "N/A")

# Test Login
response = client.post('/login', data={
    'phone': '01234567890',
    'password': 'password123'
}, follow_redirects=True)

print("Login status code:", response.status_code)
html = response.data.decode('utf-8')
if "Real Student" in html:
    print("Login successful - found student name in HTML.")
if "تسجيل الخروج" in html:
    print("Login successful - found logout button.")
