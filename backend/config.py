import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'goshala-care-secret-key-production-ready-2026')
    WTF_CSRF_ENABLED = True
    
    # Upload folder configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # MySQL Database credentials read strictly from environment variables
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'goshala_db')
    USE_SQLITE_FALLBACK = os.environ.get('USE_SQLITE_FALLBACK', 'true').lower() in ('1', 'true', 'yes')

    @classmethod
    def get_database_uri(cls):
        # Allow direct DATABASE_URL override if supplied
        if os.environ.get('DATABASE_URL'):
            return os.environ.get('DATABASE_URL')
            
        # Try MySQL connection string
        if cls.DB_PASSWORD:
            mysql_uri = f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"
        else:
            mysql_uri = f"mysql+pymysql://{cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"
            
        return mysql_uri

    # Model and Data paths
    MODELS_DIR = str(BASE_DIR / 'backend' / 'models')
    DATA_DIR = str(BASE_DIR / 'data')
    VITALS_DATA_DIR = str(BASE_DIR / 'data' / 'vitals')
    IMAGE_DATA_DIR = str(BASE_DIR / 'data')
    
    # Paths for frontend templates and static files inside frontend folder
    FRONTEND_DIR = BASE_DIR / 'frontend'
    TEMPLATE_FOLDER = str(BASE_DIR / 'frontend' / 'templates')
    STATIC_FOLDER = str(BASE_DIR / 'frontend' / 'static')
