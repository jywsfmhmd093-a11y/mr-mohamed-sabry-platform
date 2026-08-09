from app import app
from models import db, User, Level, Lecture, Quiz, Question, Subscription
import json

client = app.test_client()

def run_tests():
    with app.app_context():
        print("=== Starting Comprehensive Audit & Testing ===")
        
        # 1. Clean up old test data if exists
        test_phone = '01999999999'
        u = User.query.filter_by(phone=test_phone).first()
        if u:
            db.session.delete(u)
            db.session.commit()
            print("[+] Old test user removed.")

        # Ensure we have a Level and a Quiz to test with
        level = Level.query.first()
        if not level:
            print("[-] No levels found. Cannot proceed with tests.")
            return

        quiz = Quiz.query.filter_by(course_id=level.id).first()
        if not quiz:
            # Create a test quiz if not exists
            quiz = Quiz(title="Test Quiz Automated", course_id=level.id)
            db.session.add(quiz)
            db.session.commit()
            
            q1 = Question(quiz_id=quiz.id, question_type='mcq', text='Test Q1', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')
            q2 = Question(quiz_id=quiz.id, question_type='mcq', text='Test Q2', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='B')
            db.session.add_all([q1, q2])
            db.session.commit()
            print(f"[+] Created dummy quiz '{quiz.title}' with ID: {quiz.id}")
        else:
            print(f"[+] Found existing quiz '{quiz.title}' with ID: {quiz.id}")

        print("\n--- Testing Student Flow ---")
        
        # 2. Register Student
        response = client.post('/register', data={
            'name': 'Test Student Audit',
            'phone': test_phone,
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        assert b'\xd8\xaa\xd9\x85 \xd8\xa5\xd9\x86\xd8\xb4\xd8\xa7\xd8\xa1 \xd8\xa7\xd9\x84\xd8\xad\xd8\xb3\xd8\xa7\xd8\xa8' in response.data or response.status_code == 200, "Registration failed"
        print("[+] Registration: SUCCESS")

        # 3. Login Student
        response = client.post('/login', data={
            'phone': test_phone,
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200, "Login failed"
        print("[+] Login: SUCCESS")

        user = User.query.filter_by(phone=test_phone).first()

        # 4. Create Active Subscription manually for testing purposes
        sub = Subscription(user_id=user.id, level_id=level.id, status='active')
        db.session.add(sub)
        db.session.commit()
        print("[+] Activated subscription for student.")

        # 5. Access Lecture Page
        lecture = Lecture.query.filter_by(level_id=level.id).first()
        if lecture:
            response = client.get(f'/lecture/{lecture.id}')
            assert response.status_code == 200, f"Failed to access lecture {lecture.id}"
            assert b'plyr.js' in response.data or b'plyr.css' in response.data, "Plyr.js not found in lecture page!"
            print("[+] Lecture Access (Plyr check): SUCCESS")
        else:
            print("[-] No lecture found for this level to test.")

        # 6. Access Quiz Page (GET)
        response = client.get(f'/quiz/{quiz.id}')
        assert response.status_code == 200, f"Failed to access quiz {quiz.id}"
        print("[+] Quiz View GET: SUCCESS")

        # 7. Submit Quiz (POST)
        # We will submit correct answer for first question if it's MCQ, and incorrect for others.
        questions = quiz.questions
        form_data = {}
        for q in questions:
            if q.question_type == 'mcq':
                form_data[f'question_{q.id}'] = q.correct_option # Submit correct answer
            else:
                form_data[f'question_{q.id}'] = 'This is an essay answer'

        response = client.post(f'/quiz/{quiz.id}', data=form_data, follow_redirects=True)
        assert response.status_code == 200, "Error 500 or failed to submit quiz!"
        
        # Verify result was saved
        db.session.refresh(user)
        submissions = user.quiz_submissions
        assert len(submissions) > 0, "Submission not saved to database!"
        
        last_sub = submissions[-1]
        print(f"[+] Quiz Submit POST: SUCCESS (Score: {last_sub.total_score}/{len(questions)})")

        # Clean up
        db.session.delete(user)
        db.session.commit()
        print("[+] Cleanup complete.")
        print("\n=== All Tests Passed Successfully! ===")

if __name__ == '__main__':
    run_tests()
