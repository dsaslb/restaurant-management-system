from flask import Flask, redirect, url_for, flash, request, render_template
from dotenv import load_dotenv
from extensions import db, migrate, login_manager
import os
from flask_cors import CORS
from config import Config
from scheduler.tasks import init_scheduler, get_scheduler_status
import logging
from logging.handlers import RotatingFileHandler
import atexit
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from models import User, Employee
from routes.auth import auth_bp, create_admin_user
from routes.employee import employee_bp
from routes.inventory import inventory_bp
from routes.order import bp as order_bp
from routes.schedule import schedule_bp
from routes.main import main_bp
from datetime import datetime, timedelta

# 환경 변수 로드
load_dotenv()

# 로깅 설정
if not os.path.exists('logs'):
    os.mkdir('logs')

# 파일 핸들러 설정
file_handler = RotatingFileHandler('logs/restaurant_system.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
console_handler.setLevel(logging.INFO)

# 루트 로거 설정
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

# 앱 인스턴스 생성
app = Flask(__name__)
app.config.from_object(Config)

# 세션 설정
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경에서는 False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False  # 개발 환경에서는 False
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# CORS 설정
CORS(app)

# 데이터베이스 초기화
db.init_app(app)
migrate.init_app(app, db)

# 로그인 매니저 초기화
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """사용자 로더 콜백"""
    return User.query.get(int(user_id))

def create_admin():
    """관리자 계정 생성"""
    try:
        # 기존 admin01 계정이 있다면 삭제
        admin = User.query.filter_by(username='admin01').first()
        if admin:
            db.session.delete(admin)
            db.session.commit()
            logger.info('기존 관리자 계정이 삭제되었습니다.')
        
        # 새로운 admin01 계정 생성
        admin = User(
            username='admin01',
            email='admin@example.com',
            role='admin',
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()
        logger.info('새로운 관리자 계정이 생성되었습니다.')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"관리자 계정 생성 중 오류 발생: {str(e)}")
        raise

# 메인 페이지 라우트
@app.route('/')
def index():
    """메인 페이지"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('index.html')

# 블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(order_bp)
app.register_blueprint(schedule_bp)

# 스케줄러 초기화
scheduler = BackgroundScheduler()
init_scheduler(scheduler)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# 데이터베이스 초기화 및 관리자 계정 생성
with app.app_context():
    db.drop_all()  # 기존 데이터베이스 삭제
    db.create_all()  # 새로운 데이터베이스 생성
    create_admin()  # 관리자 계정 생성

if __name__ == '__main__':
    logger.info('레스토랑 시스템 시작')
    app.run(host='0.0.0.0', port=8080, debug=True)


