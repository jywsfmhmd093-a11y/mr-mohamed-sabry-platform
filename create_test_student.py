from app import app
from models import db, User, Level, Subscription

with app.app_context():
    phone = '01000000000'
    password = '123456'
    name = 'طالب تجريبي'
    level_name = 'الصف الثالث الثانوي'
    
    # Check if student exists
    student = User.query.filter_by(phone=phone).first()
    if not student:
        student = User(name=name, phone=phone, role='student')
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        print("Created new student.")
    else:
        student.set_password(password)
        student.name = name
        student.role = 'student'
        db.session.commit()
        print("Updated existing student.")
        
    # Check if level exists
    level = Level.query.filter_by(title=level_name).first()
    if not level:
        level = Level(title=level_name, description='test', image_url='/static/images/pyramids.jpg')
        db.session.add(level)
        db.session.commit()
        print("Created new level.")
        
    # Subscribe student to level
    sub = Subscription.query.filter_by(user_id=student.id, level_id=level.id).first()
    if not sub:
        sub = Subscription(user_id=student.id, level_id=level.id, status='active')
        db.session.add(sub)
        db.session.commit()
        print("Created active subscription.")
    elif sub.status != 'active':
        sub.status = 'active'
        db.session.commit()
        print("Updated subscription to active.")
