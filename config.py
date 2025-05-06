import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """기본 설정"""
    # 기본 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    JWT_SECRET_KEY = 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # 데이터베이스 설정
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///restaurant.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # POS 시스템 설정
    POS_API_URL = os.getenv('POS_API_URL', 'http://localhost:5001/api')
    POS_API_KEY = os.getenv('POS_API_KEY', 'test_key')
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/restaurant.log')
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_MAX_BYTES = 10240
    LOG_BACKUP_COUNT = 10
    
    # 세션 설정
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30분
    
    # 업로드 설정
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # 보안 설정
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # 카카오 알림톡 설정
    KAKAO_REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY', 'your-kakao-rest-api-key')
    KAKAO_TEMPLATE_ID = os.environ.get('KAKAO_TEMPLATE_ID', 'your-kakao-template-id')
    
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# 카카오 API 설정
KAKAO_ACCESS_TOKEN = os.environ.get('KAKAO_ACCESS_TOKEN')
KAKAO_SENDER_KEY = os.environ.get('KAKAO_SENDER_KEY')
KAKAO_API_KEY = os.environ.get('KAKAO_API_KEY')

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # 운영 환경에서는 반드시 환경 변수로 설정
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 