from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.name} - {self.phone}>"


class Level(db.Model):
    __tablename__ = 'levels'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)  # Price in EGP
    image_url = db.Column(db.String(300), nullable=True)  # Thumbnail url
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lectures = db.relationship('Lecture', backref='level', lazy=True, cascade="all, delete-orphan", order_by="Lecture.sort_order")
    subscriptions = db.relationship('Subscription', backref='level', lazy=True, cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Level {self.title} - {self.price} EGP>"


class Lecture(db.Model):
    __tablename__ = 'lectures'
    
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=False)  # Bunny.net / YouTube / Vimeo embedded link
    sort_order = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Lecture {self.title} (Order: {self.sort_order})>"


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz {self.title}>"


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default='mcq') # 'mcq' or 'essay'
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Question {self.id} ({self.question_type})>"


class QuizSubmission(db.Model):
    __tablename__ = 'quiz_submissions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='graded') # 'graded', 'pending_grading'
    total_score = db.Column(db.Float, nullable=False, default=0.0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', backref=db.backref('quiz_submissions', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('submissions', lazy=True))
    answers = db.relationship('StudentAnswer', backref='submission', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QuizSubmission {self.id} User:{self.user_id} Status:{self.status}>"


class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('quiz_submissions.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    
    selected_option = db.Column(db.String(10), nullable=True) # for mcq
    answer_text = db.Column(db.Text, nullable=True)           # for essay
    
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)                  # Teacher can give points for essay, or 1 for mcq
    
    question = db.relationship('Question')

    def __repr__(self):
        return f"<StudentAnswer Sub:{self.submission_id} Q:{self.question_id}>"


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'active'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payment_proofs = db.relationship('PaymentProof', backref='subscription', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'level_id', name='uq_user_level_subscription'),
    )

    def __repr__(self):
        return f"<Subscription User:{self.user_id} Level:{self.level_id} Status:{self.status}>"


class PaymentProof(db.Model):
    __tablename__ = 'payment_proofs'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentProof Sub:{self.subscription_id} File:{self.image_filename}>"


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.String(50), nullable=True)    # Store as string e.g. "2026-09-01"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    level = db.relationship('Level', backref=db.backref('assignments', lazy=True, cascade='all, delete-orphan'))
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Assignment {self.title}>"


class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    file_filename = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.String(20), nullable=True)       # Admin can grade: "10/10", "جيد", etc.
    feedback = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship('User', backref=db.backref('submissions', lazy=True))

    def __repr__(self):
        return f"<AssignmentSubmission Assign:{self.assignment_id} User:{self.user_id}>"

