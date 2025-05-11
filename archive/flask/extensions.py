from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# SQLAlchemy 인스턴스 생성
db = SQLAlchemy()

# Migrate 인스턴스 생성
migrate = Migrate()

# LoginManager 인스턴스 생성
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '로그인이 필요합니다.'

# 요청 제한
limiter = Limiter(key_func=get_remote_address)

# CORS
cors = CORS()

def init_extensions(app):
    """Flask 확장 모듈 초기화"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    cors.init_app(app) 