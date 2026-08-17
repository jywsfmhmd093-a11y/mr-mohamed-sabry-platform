from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os
from datetime import datetime

from config import Config
from models import db, User, Level, Lecture, Subscription, PaymentProof, Quiz, Question, Assignment, AssignmentSubmission, QuizSubmission, StudentAnswer

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول أولاً للوصول إلى هذا المحتوى.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})

def resolve_level_image_url(image_url, title=None):
    if image_url and image_url.strip():
        return image_url

    title_text = (title or '').lower()
    if 'جغراف' in title_text or 'geograph' in title_text:
        return '/static/images/geography.jpg'
    if 'ثالث' in title_text or 'third' in title_text:
        return '/static/images/sphinx.jpg'
    if 'النيل' in title_text or 'nile' in title_text:
        return '/static/images/nile.jpg'
    return '/static/images/pyramids.jpg'

def normalize_video_url(video_url):
    if not video_url:
        return video_url

    video_url = video_url.strip()

    if 'youtube.com/watch?v=' in video_url:
        video_id = video_url.split('v=')[1].split('&')[0]
        return f'https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&controls=1&showinfo=0'

    if 'youtu.be/' in video_url:
        video_id = video_url.split('/')[-1].split('?')[0]
        return f'https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1&controls=1&showinfo=0'

    if 'youtube.com/embed/' in video_url:
        separator = '&' if '?' in video_url else '?'
        if 'modestbranding=' not in video_url:
            video_url = f'{video_url}{separator}modestbranding=1'
            separator = '&'
        if 'rel=' not in video_url:
            video_url = f'{video_url}{separator}rel=0'
            separator = '&'
        if 'showinfo=' not in video_url:
            video_url = f'{video_url}{separator}showinfo=0'
            separator = '&'
        if 'controls=' not in video_url:
            video_url = f'{video_url}{separator}controls=1'
        return video_url

    return video_url

@app.context_processor
def inject_global_data():
    return {
        'now': datetime.utcnow()
    }

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    upload_dir = app.config.get('UPLOAD_FOLDER', '/tmp/uploads')
    return send_from_directory(upload_dir, filename)

# --- PUBLIC ROUTES ---

@app.route('/')
def index():
    try:
        levels = Level.query.all()
        stats = {
            'students': User.query.filter_by(role='student').count() + 1420,
            'lectures': Lecture.query.count() + 85,
            'levels': Level.query.count()
        }
    except Exception:
        levels = []
        stats = {'students': 1420, 'lectures': 85, 'levels': 0}
    return redirect(url_for('login'))

@app.route('/level/<int:level_id>')
def level_detail(level_id):
    level = Level.query.get_or_404(level_id)
    subscription = None
    if current_user.is_authenticated:
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            level_id=level.id
        ).first()
        
    return render_template('level_detail.html', level=level, subscription=subscription)

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not phone or not password:
            flash('يرجى ملء جميع الحقول المطلوبة.', 'danger')
            return redirect(url_for('register'))
            
        if len(phone) < 10:
            flash('يرجى إدخال رقم هاتف صحيح.', 'danger')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('كلمتا المرور غير متطابقتين.', 'danger')
            return redirect(url_for('register'))
            
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash('رقم الهاتف مسجل بالفعل. يرجى تسجيل الدخول.', 'warning')
            return redirect(url_for('login'))
            
        new_user = User(name=name, phone=phone, role='student')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    next_page = request.args.get('next')
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone=phone).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'مرحباً بك يا {user.name}!', 'success')
            
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('رقم الهاتف أو كلمة المرور غير صحيحة.', 'danger')
            
    return render_template('login.html', next=next_page)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('index'))

# --- STUDENT DASHBOARD ROUTE ---

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    levels = Level.query.all()
    user_subscriptions = {sub.level_id: sub for sub in current_user.subscriptions}
    
    active_subscriptions_count = sum(1 for sub in current_user.subscriptions if sub.status == 'active')
    pending_subscriptions_count = sum(1 for sub in current_user.subscriptions if sub.status == 'pending')
    
    progress = 0
    if len(levels) > 0:
        progress = int((active_subscriptions_count / len(levels)) * 100)
        
    active_level_ids = [sub.level_id for sub in current_user.subscriptions if sub.status == 'active']
    
    upcoming_assignments = Assignment.query.filter(Assignment.level_id.in_(active_level_ids)).order_by(Assignment.created_at.desc()).limit(3).all() if active_level_ids else []
    upcoming_quizzes = Quiz.query.filter(Quiz.course_id.in_(active_level_ids)).order_by(Quiz.id.desc()).limit(3).all() if active_level_ids else []

    return render_template('dashboard.html', 
                           levels=levels, 
                           user_subscriptions=user_subscriptions, 
                           progress=progress,
                           active_count=active_subscriptions_count,
                           pending_count=pending_subscriptions_count,
                           upcoming_assignments=upcoming_assignments,
                           upcoming_quizzes=upcoming_quizzes)

@app.route('/subscribe/<int:level_id>', methods=['POST'])
@login_required
def subscribe(level_id):
    level = Level.query.get_or_404(level_id)
    existing_sub = Subscription.query.filter_by(user_id=current_user.id, level_id=level.id).first()
    
    if 'payment_proof' not in request.files:
        flash('يرجى اختيار صورة إثبات الدفع.', 'danger')
        return redirect(url_for('dashboard'))
        
    file = request.files['payment_proof']
    if file.filename == '':
        flash('لم يتم تحديد أي ملف.', 'danger')
        return redirect(url_for('dashboard'))
        
    if file and allowed_file(file.filename):
        upload_dir = app.config.get('UPLOAD_FOLDER', '/tmp/uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(f"proof_{current_user.id}_{level.id}_{int(datetime.utcnow().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        if existing_sub:
            existing_sub.status = 'pending'
            for proof in existing_sub.payment_proofs:
                db.session.delete(proof)
            db.session.commit()
            sub = existing_sub
        else:
            sub = Subscription(user_id=current_user.id, level_id=level.id, status='pending')
            db.session.add(sub)
            db.session.commit()
            
        proof = PaymentProof(subscription_id=sub.id, image_filename=filename)
        db.session.add(proof)
        db.session.commit()
        
        flash('تم رفع إثبات الدفع بنجاح! سيتم تفعيل الكورس لك بعد مراجعة المستر للدفع.', 'success')
    else:
        flash('نوع الملف غير مسموح به. يرجى رفع صورة فقط (JPG, PNG, WEBP).', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/lecture/<int:lecture_id>')
@login_required
def watch_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    level = lecture.level
    
    if current_user.role != 'admin':
        sub = Subscription.query.filter_by(user_id=current_user.id, level_id=level.id).first()
        if not sub or sub.status != 'active':
            flash('هذا المحتوى مغلق. يرجى الاشتراك أولاً لتتمكن من المشاهدة.', 'warning')
            return redirect(url_for('level_detail', level_id=level.id))
            
    lectures = Lecture.query.filter_by(level_id=level.id).order_by(Lecture.sort_order).all()
    lecture.video_url = normalize_video_url(lecture.video_url)
    return render_template('lecture.html', lecture=lecture, level=level, lectures=lectures)

@app.route('/quizzes')
@login_required
def quizzes():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    active_levels = [sub.level_id for sub in current_user.subscriptions if sub.status == 'active']
    quizzes = Quiz.query.filter(Quiz.course_id.in_(active_levels)).order_by(Quiz.id.desc()).all() if active_levels else []
    return render_template('quizzes.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    subscription = Subscription.query.filter_by(user_id=current_user.id, level_id=quiz.course_id, status='active').first()
    if not subscription:
        flash('لا يمكنك حل هذا الاختبار إلا إذا كنت مشتركًا نشطًا في هذا الكورس.', 'warning')
        return redirect(url_for('quizzes'))

    if request.method == 'POST':
        submission = QuizSubmission(quiz_id=quiz.id, user_id=current_user.id, status='graded', total_score=0.0)
        db.session.add(submission)
        db.session.flush()

        score = 0
        total = len(quiz.questions)
        
        if total == 0:
            flash('لا يمكن تقديم هذا الاختبار لعدم وجود أسئلة مسجلة به.', 'warning')
            return redirect(url_for('quizzes'))
            
        has_essay = False

        for question in quiz.questions:
            answer = StudentAnswer(submission_id=submission.id, question_id=question.id)
            if question.question_type == 'essay':
                has_essay = True
                answer.answer_text = request.form.get(f'question_{question.id}', '').strip()
                answer.is_correct = False
                answer.score = 0.0
            else:
                selected = request.form.get(f'question_{question.id}')
                answer.selected_option = selected
                if selected and selected == question.correct_option:
                    answer.is_correct = True
                    answer.score = 1.0
                    score += 1
                else:
                    answer.is_correct = False
                    answer.score = 0.0
            db.session.add(answer)

        submission.total_score = float(score)
        if has_essay:
            submission.status = 'pending_grading'
            
        db.session.commit()
        
        percent = int((score / total) * 100) if total else 0
        return render_template('quiz_result.html', quiz=quiz, score=score, total=total, percent=percent, submission=submission)

    return render_template('quiz_take.html', quiz=quiz)

# --- ADMIN ROUTES ---

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
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
    
    students = (
        User.query.filter_by(role='student')
        .order_by(User.created_at.desc())
        .options(joinedload(User.subscriptions).joinedload(Subscription.level))
        .all()
    )
    
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    all_submissions = AssignmentSubmission.query.order_by(AssignmentSubmission.submitted_at.desc()).all()
    pending_quizzes = QuizSubmission.query.filter_by(status='pending_grading').order_by(QuizSubmission.submitted_at.desc()).all()

    return render_template('admin.html',
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

@app.route('/admin/level/add', methods=['POST'])
@login_required
@admin_required
def admin_add_level():
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    image_url = request.form.get('image_url')
    
    if not title or not price:
        flash('يرجى إدخال اسم المستوى وسعر الاشتراك.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    try:
        price = float(price)
    except ValueError:
        flash('سعر الاشتراك يجب أن يكون رقماً صحيحاً.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    image_url = resolve_level_image_url(image_url, title)
    
    new_level = Level(title=title, description=description, price=price, image_url=image_url)
    db.session.add(new_level)
    db.session.commit()
    
    flash('تم إضافة المستوى الدراسي بنجاح!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/level/delete/<int:level_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_level(level_id):
    level = Level.query.get_or_404(level_id)
    db.session.delete(level)
    db.session.commit()
    flash('تم حذف المستوى بجميع محاضراته وااشتراكاته بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/add', methods=['POST'])
@login_required
@admin_required
def admin_add_quiz():
    title = request.form.get('title', '').strip()
    course_id = request.form.get('course_id')

    if not title or not course_id:
        flash('يرجى إدخال عنوان الاختبار وتحديد الكورس.', 'danger')
        return redirect(url_for('admin_dashboard'))

    quiz = Quiz(title=title, course_id=int(course_id))
    db.session.add(quiz)
    db.session.commit()
    flash('تم إضافة الاختبار بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/quiz/question/add', methods=['POST'])
@login_required
@admin_required
def admin_add_question():
    quiz_id = request.form.get('quiz_id')
    question_type = request.form.get('question_type', 'mcq')
    text = request.form.get('question_text', '').strip()
    
    if question_type == 'mcq':
        option_a = request.form.get('option_a', '').strip()
        option_b = request.form.get('option_b', '').strip()
        option_c = request.form.get('option_c', '').strip()
        option_d = request.form.get('option_d', '').strip()
        correct_option = request.form.get('correct_option', '').strip().upper()
        if not all([quiz_id, text, option_a, option_b, option_c, option_d, correct_option]):
            return {"success": False, "message": "يرجى ملء جميع حقول السؤال والإجابات."}, 400
    else:
        option_a = option_b = option_c = option_d = correct_option = None
        if not all([quiz_id, text]):
            return {"success": False, "message": "يرجى ملء نص السؤال."}, 400

    question = Question(
        quiz_id=int(quiz_id),
        question_type=question_type,
        text=text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
    )
    db.session.add(question)
    db.session.commit()
    return {"success": True, "message": "تم إضافة السؤال بنجاح."}, 200

@app.route('/admin/quiz/grade/<int:submission_id>', methods=['POST'])
@login_required
@admin_required
def admin_grade_quiz_submission(submission_id):
    sub = QuizSubmission.query.get_or_404(submission_id)
    
    added_score = 0.0
    for answer in sub.answers:
        if answer.question.question_type == 'essay':
            score_val = request.form.get(f'score_{answer.id}', '0').strip()
            try:
                score_val = float(score_val)
            except ValueError:
                score_val = 0.0
            answer.score = score_val
            added_score += score_val
            
    sub.total_score += added_score
    sub.status = 'graded'
    db.session.commit()
    
    flash(f'تم تصحيح امتحان الطالب {sub.student.name} بنجاح.', 'success')
    return redirect(url_for('admin_dashboard') + '#quizzes')

@app.route('/admin/lecture/add', methods=['POST'])
@login_required
@admin_required
def admin_add_lecture():
    level_id = request.form.get('level_id')
    title = request.form.get('title')
    description = request.form.get('description')
    video_url = request.form.get('video_url')
    sort_order = request.form.get('sort_order', 1)
    
    if not level_id or not title or not video_url:
        flash('يرجى ملء جميع الحقول الإجبارية للمحاضرة.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    video_url = normalize_video_url(video_url)
    
    new_lecture = Lecture(
        level_id=int(level_id),
        title=title,
        description=description,
        video_url=video_url,
        sort_order=int(sort_order)
    )
    db.session.add(new_lecture)
    db.session.commit()
    
    flash('تم إضافة المحاضرة للمستوى بنجاح!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/level/update/<int:level_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_level(level_id):
    level = Level.query.get_or_404(level_id)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    price = request.form.get('price', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not title and not price and not description and not image_url:
        flash('يرجى إدخال بيانات على الأقل للتحديث.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if title:
        level.title = title
    if description is not None:
        level.description = description
    if image_url:
        level.image_url = image_url

    if price:
        try:
            level.price = float(price)
        except ValueError:
            flash('سعر الاشتراك يجب أن يكون رقماً صحيحاً.', 'danger')
            return redirect(url_for('admin_dashboard'))

    db.session.commit()
    flash('تم تحديث بيانات المستوى بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/lecture/delete/<int:lecture_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    db.session.delete(lecture)
    db.session.commit()
    flash('تم حذف المحاضرة بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/subscription/activate/<int:sub_id>', methods=['POST'])
@login_required
@admin_required
def admin_activate_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    sub.status = 'active'
    db.session.commit()
    flash(f'تم تفعيل اشتراك الطالب {sub.user.name} في مستوى "{sub.level.title}" بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/subscription/deactivate/<int:sub_id>', methods=['POST'])
@login_required
@admin_required
def admin_deactivate_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    flash('تم إلغاء الاشتراك بنجاح.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assignment/add', methods=['POST'])
@login_required
@admin_required
def admin_add_assignment():
    level_id = request.form.get('level_id')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = request.form.get('due_date', '').strip()

    if not level_id or not title:
        flash('يرجى اختيار المستوى الدراسي وكتابة عنوان الواجب.', 'danger')
        return redirect(url_for('admin_dashboard'))

    assignment = Assignment(
        level_id=int(level_id),
        title=title,
        description=description,
        due_date=due_date or None
    )
    db.session.add(assignment)
    db.session.commit()
    flash('تم إضافة الواجب بنجاح!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assignment/delete/<int:assignment_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash('تم حذف الواجب وجميع إجابات الطلاب المرتبطة به.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/submission/grade/<int:submission_id>', methods=['POST'])
@login_required
@admin_required
def admin_grade_submission(submission_id):
    sub = AssignmentSubmission.query.get_or_404(submission_id)
    sub.grade = request.form.get('grade', '').strip()
    sub.feedback = request.form.get('feedback', '').strip()
    db.session.commit()
    flash(f'تم تقييم إجابة الطالب {sub.student.name} بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- STUDENT ASSIGNMENT ROUTES ---

@app.route('/assignments')
@login_required
def student_assignments():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    active_level_ids = [sub.level_id for sub in current_user.subscriptions if sub.status == 'active']
    assignments = Assignment.query.filter(Assignment.level_id.in_(active_level_ids)).order_by(Assignment.created_at.desc()).all() if active_level_ids else []
    submitted_ids = {s.assignment_id for s in current_user.submissions}
    return render_template('assignments.html', assignments=assignments, submitted_ids=submitted_ids)

@app.route('/assignment/submit/<int:assignment_id>', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role == 'admin':
        abort(403)
    assignment = Assignment.query.get_or_404(assignment_id)
    sub = Subscription.query.filter_by(user_id=current_user.id, level_id=assignment.level_id, status='active').first()
    if not sub:
        flash('لا يمكنك تسليم هذا الواجب. يجب الاشتراك في الكورس أولاً.', 'warning')
        return redirect(url_for('student_assignments'))

    answer_text = request.form.get('answer_text', '').strip()
    existing = AssignmentSubmission.query.filter_by(assignment_id=assignment_id, user_id=current_user.id).first()
    if existing:
        existing.answer_text = answer_text
        existing.submitted_at = datetime.utcnow()
        db.session.commit()
        flash('تم تحديث إجابتك بنجاح.', 'success')
    else:
        new_sub = AssignmentSubmission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            answer_text=answer_text
        )
        db.session.add(new_sub)
        db.session.commit()
        flash('تم تسليم الواجب بنجاح! سيقوم المستر بالتصحيح قريباً.', 'success')
    return redirect(url_for('student_assignments'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
