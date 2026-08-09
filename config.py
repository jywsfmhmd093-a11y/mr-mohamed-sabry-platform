import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mr-mohamed-sabry-secret-key-2024')
    
    # استخدام المجلد المؤقت /tmp الخاص بـ Vercel لقواعد البيانات والملفات
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # تحديد مسار قاعدة البيانات في /tmp لمنع أخطاء Read-only filesystem
    DB_PATH = os.path.join('/tmp', 'platform.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تحديد مجلد المرفقات وإثباتات الدفع في /tmp
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
