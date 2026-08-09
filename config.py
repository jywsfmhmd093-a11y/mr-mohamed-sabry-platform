import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mr-mohamed-sabry-secret-key-2024')
    
    # مسار قاعدة البيانات والملفات في المجلد المؤقت /tmp لتوافق بيئة Vercel
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = '/tmp/platform.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # مجلد المرفقات وإثباتات الدفع
    UPLOAD_FOLDER = '/tmp/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
