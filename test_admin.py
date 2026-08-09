from app import app
from flask import render_template
from models import db, User, Level, Lecture, Subscription, Quiz, Assignment, AssignmentSubmission, QuizSubmission
from sqlalchemy.orm import joinedload
import traceback

with app.app_context():
    with app.test_request_context('/admin'):
        try:
            students_count = User.query.filter_by(role='student').count()
            levels_count = Level.query.count()
            lectures_count = Lecture.query.count()
            active_subs_count = Subscription.query.filter_by(status='active').count()
            pending_subs_count = Subscription.query.filter_by(status='pending').count()
            
            levels = Level.query.order_by(Level.id.asc()).all()
            pending_subscriptions = (
                Subscription.query.filter_by(status='pending')
                .options(joinedload(Subscription.user), joinedload(Subscription.level), joinedload(Subscription.payment_proofs))
                .all()
            )
            quizzes = Quiz.query.order_by(Quiz.id.desc()).all()
            
            # Students list
            students = (
                User.query.filter_by(role='student')
                .order_by(User.created_at.desc())
                .options(joinedload(User.subscriptions).joinedload(Subscription.level))
                .all()
            )
            
            assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
            # All submissions for admin review
            all_submissions = AssignmentSubmission.query.order_by(AssignmentSubmission.submitted_at.desc()).all()
            
            # Quiz submissions that are pending grading
            pending_quizzes = QuizSubmission.query.filter_by(status='pending_grading').order_by(QuizSubmission.submitted_at.desc()).all()

            # Mock current_user
            app.jinja_env.globals['current_user'] = User.query.filter_by(role='admin').first()

            html = render_template('admin.html',
                                   students_count=students_count,
                                   levels_count=levels_count,
                                   lectures_count=lectures_count,
                                   active_subs_count=active_subs_count,
                                   pending_subs_count=pending_subs_count,
                                   levels=levels,
                                   pending_subscriptions=pending_subscriptions,
                                   students=students,
                                   quizzes=quizzes,
                                   assignments=assignments,
                                   all_submissions=all_submissions,
                                   pending_quizzes=pending_quizzes)
            print("Render successful, length:", len(html))
        except Exception as e:
            traceback.print_exc()
