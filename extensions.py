from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# SQLAlchemy 인스턴스 생성
db = SQLAlchemy()

# Migrate 인스턴스 생성
migrate = Migrate()

# LoginManager 인스턴스 생성
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '로그인이 필요한 페이지입니다.'

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db) 