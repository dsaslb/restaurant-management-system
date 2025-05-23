from flask import Flask, redirect, url_for, flash, request, render_template
from markupsafe import Markup
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
from flask_login import LoginManager, current_user, login_required, logout_user
from utils.logger import setup_logger
from supabase import create_client, Client

from models import (
    User,
    Employee,
    Supplier,
    Order,
    OrderItem,
    ProductCategory,
    InventoryStatus,
    InventoryItem,
    InventoryBatch,
    Ingredient,
    StockItem,
    StockTransaction,
    StockUsageAlert,
    Inventory,
    Disposal,
    Schedule,
    ScheduleHistory,
    Notification,
    AlertLog,
    Attendance,
    Contract,
    ContractTemplate,
)

from routes.auth import auth_bp, create_admin_user
from routes.employee import employee_bp
from routes.inventory import inventory_bp
from routes.order import order_bp
from routes.schedule import schedule_bp
from routes.main import main_bp
from routes.suppliers import supplier_bp
from routes.notification import notification_bp
from routes.employees import employees_bp
from routes.orders import order_bp
from datetime import datetime, timedelta
from routes.contracts import contract_bp
from routes.attendance import attendance_bp
from routes.admin import admin_bp
from routes.staff import staff_bp

# 환경 변수 로드
load_dotenv()

# 앱 인스턴스 생성
app = Flask(__name__)
app.config.from_object(Config)

# 로깅 설정
if not os.path.exists('logs'):
    os.mkdir('logs')

# 파일 핸들러 설정
file_handler = RotatingFileHandler('logs/restaurant_system_new.log', maxBytes=10240, backupCount=10)
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
logger = setup_logger('restaurant_system')  # 문자열 이름을 전달

# 템플릿 자동 리로드 설정
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
migrate = Migrate(app, db)

# 로그인 매니저 초기화
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'
login_manager.login_message_category = 'info'

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
            # 해당 관리자와 연결된 주문 데이터 삭제
            Order.query.filter_by(user_id=admin.id).delete()
            db.session.commit()
            
            # 관리자 계정 삭제
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

def create_sample_data():
    """예시 데이터 생성"""
    # 관리자 계정 생성
    admin = User.query.filter_by(username='admin01').first()
    if not admin:
        admin = User(
            username='admin01',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()
    
    # 직원 계정 생성
    employees = [
        {
            'username': 'emp01',
            'email': 'emp01@example.com',
            'name': '김철수',
            'position': '주방장',
            'phone': '010-1234-5678',
            'hire_date': datetime.now() - timedelta(days=365)
        },
        {
            'username': 'emp02',
            'email': 'emp02@example.com',
            'name': '이영희',
            'position': '서빙',
            'phone': '010-2345-6789',
            'hire_date': datetime.now() - timedelta(days=180)
        },
        {
            'username': 'emp03',
            'email': 'emp03@example.com',
            'name': '박지민',
            'position': '주방보조',
            'phone': '010-3456-7890',
            'hire_date': datetime.now() - timedelta(days=90)
        },
        {
            'username': 'emp04',
            'email': 'emp04@example.com',
            'name': '최수진',
            'position': '매니저',
            'phone': '010-4567-8901',
            'hire_date': datetime.now() - timedelta(days=60)
        },
        {
            'username': 'emp05',
            'email': 'emp05@example.com',
            'name': '정민호',
            'position': '주방보조',
            'phone': '010-5678-9012',
            'hire_date': datetime.now() - timedelta(days=30)
        }
    ]
    
    for emp_data in employees:
        user = User.query.filter_by(username=emp_data['username']).first()
        if not user:
            user = User(
                username=emp_data['username'],
                email=emp_data['email'],
                role='user'
            )
            user.set_password('1234')
            db.session.add(user)
            db.session.flush()
            
            employee = Employee(
                user_id=user.id,
                name=emp_data['name'],
                email=emp_data['email'],
                position=emp_data['position'],
                phone=emp_data['phone'],
                hire_date=emp_data['hire_date']
            )
            db.session.add(employee)
    
    db.session.commit()
    
    # 공급업체 생성
    suppliers = [
        {
            'name': '신선식품',
            'contact': '02-123-4567',
            'order_method': 'email',
            'email': 'fresh@example.com',
            'address': '서울시 강남구 신선로 123'
        },
        {
            'name': '건어물상사',
            'contact': '02-234-5678',
            'order_method': 'web',
            'email': 'seafood@example.com',
            'address': '서울시 서초구 건어물로 456'
        },
        {
            'name': '청과물도매',
            'contact': '02-345-6789',
            'order_method': 'sms',
            'email': 'fruit@example.com',
            'address': '서울시 송파구 청과로 789'
        },
        {
            'name': '육류도매',
            'contact': '02-456-7890',
            'order_method': 'phone',
            'email': 'meat@example.com',
            'address': '서울시 마포구 육류로 101'
        },
        {
            'name': '양념도매',
            'contact': '02-567-8901',
            'order_method': 'email',
            'email': 'spice@example.com',
            'address': '서울시 용산구 양념로 202'
        }
    ]
    
    for sup_data in suppliers:
        supplier = Supplier.query.filter_by(name=sup_data['name']).first()
        if not supplier:
            supplier = Supplier(**sup_data)
            db.session.add(supplier)
    
    db.session.commit()
    
    # 재고 품목 생성
    items = [
        {
            'name': '돼지고기',
            'category': '육류',
            'unit': 'kg',
            'min_quantity': 10,
            'current_quantity': 20,
            'unit_price': 15000,
            'supplier_id': 4  # 육류도매
        },
        {
            'name': '쌀',
            'category': '식자재',
            'unit': 'kg',
            'min_quantity': 50,
            'current_quantity': 100,
            'unit_price': 5000,
            'supplier_id': 1  # 신선식품
        },
        {
            'name': '소고기',
            'category': '육류',
            'unit': 'kg',
            'min_quantity': 5,
            'current_quantity': 10,
            'unit_price': 30000,
            'supplier_id': 4  # 육류도매
        },
        {
            'name': '고춧가루',
            'category': '양념',
            'unit': 'kg',
            'min_quantity': 3,
            'current_quantity': 5,
            'unit_price': 20000,
            'supplier_id': 5  # 양념도매
        },
        {
            'name': '된장',
            'category': '양념',
            'unit': 'kg',
            'min_quantity': 2,
            'current_quantity': 4,
            'unit_price': 8000,
            'supplier_id': 5  # 양념도매
        },
        {
            'name': '고등어',
            'category': '수산물',
            'unit': '마리',
            'min_quantity': 10,
            'current_quantity': 15,
            'unit_price': 5000,
            'supplier_id': 2  # 건어물상사
        },
        {
            'name': '사과',
            'category': '과일',
            'unit': '개',
            'min_quantity': 20,
            'current_quantity': 30,
            'unit_price': 2000,
            'supplier_id': 3  # 청과물도매
        }
    ]
    
    for item_data in items:
        item = InventoryItem.query.filter_by(name=item_data['name']).first()
        if not item:
            item = InventoryItem(**item_data)
            db.session.add(item)
    
    db.session.commit()
    
    # 예시 주문 생성
    supplier = Supplier.query.first()
    if supplier:
        # 첫 번째 주문
        order1 = Order(
            user_id=admin.id,
            supplier_id=supplier.id,
            status='대기중',
            order_date=datetime.now(),
            delivery_date=datetime.now() + timedelta(days=1),
            item_name='쌀',
            category='식자재',
            quantity=100
        )
        db.session.add(order1)
        db.session.flush()
        
        # 두 번째 주문
        order2 = Order(
            user_id=admin.id,
            supplier_id=2,  # 건어물상사
            status='승인됨',
            order_date=datetime.now() - timedelta(days=1),
            delivery_date=datetime.now() + timedelta(days=1),
            item_name='고등어',
            category='수산물',
            quantity=50
        )
        db.session.add(order2)
        db.session.flush()
        
        # 주문 품목 추가
        items = InventoryItem.query.all()
        for item in items:
            order_item = OrderItem(
                order_id=order1.id,
                item_id=item.id,
                quantity=10,
                unit_price=item.unit_price,
                total_price=10 * item.unit_price
            )
            db.session.add(order_item)
            
            order_item2 = OrderItem(
                order_id=order2.id,
                item_id=item.id,
                quantity=5,
                unit_price=item.unit_price,
                total_price=5 * item.unit_price
            )
            db.session.add(order_item2)
        
        db.session.commit()

# 메인 페이지 라우트
@app.route('/')
def index():
    return redirect('/login')
    

# 블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(supplier_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(order_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(contract_bp, url_prefix='/contracts')
app.register_blueprint(attendance_bp, url_prefix='/attendance')
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)

# 스케줄러 초기화
scheduler = BackgroundScheduler()
# 스케줄러 초기화 및 시작 비활성화 (문제 해결을 위해)
# init_scheduler(scheduler)
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())

# 데이터베이스 초기화 및 관리자 계정 생성
with app.app_context():
    try:
        # 기존 데이터와의 충돌을 방지하기 위해 데이터베이스를 재생성
        db.drop_all()  # 모든 테이블 삭제
        db.create_all()  # 테이블 다시 생성
        
        # 기존 관리자 계정 생성
        admin = User(
            username='admin01',
            email='admin@example.com',
            role='admin',
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        
        # 새 총관리자 계정 생성
        super_admin = User(
            username='dsaslb@gmail.com',
            email='dsaslb@gmail.com',
            role='admin',
            is_active=True
        )
        super_admin.set_password('darkone0718!')
        db.session.add(super_admin)
        
        db.session.commit()
        logger.info('관리자 계정이 생성되었습니다.')
        logger.info('총관리자 계정이 생성되었습니다.')
        
        # 샘플 데이터 생성
        create_sample_data()
        logger.info('샘플 데이터가 생성되었습니다.')
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        db.session.rollback()

# Jinja2 필터 정의
def status_color(status):
    """주문 상태에 따라 색상을 반환합니다."""
    colors = {
        'pending': 'yellow',
        'approved': 'green',
        'rejected': 'red',
        'cancelled': 'gray',
        'received': 'blue'
    }
    return colors.get(status, 'black')

# 필터 등록
app.jinja_env.filters['status_color'] = status_color

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash('로그인 성공!')
            from flask_login import login_user
            login_user(user)
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='로그인 실패!')
    return render_template('login.html')

SUPABASE_URL = "https://ifzynlgyqdhwdcvmjogt.supabase.co" # 본인 프로젝트 URL로 변경
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmenlubGd5cWRod2Rjdm1qb2d0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NjEwMTIsImV4cCI6MjA2MjQzNzAxMn0.7yJNoNlrVscUi97qmeY83GUohyBH6V440p_HWRimYpE"             # 본인 서비스 역할 키로 변경

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_supabase_admin():
    email = "dsaslb@gmail.com"
    password = "darkone0718!"
    # 이미 존재하는지 확인
    user = supabase.auth.admin.get_user_by_email(email)
    if user.get('user'):
        print("Supabase에 이미 계정이 있습니다.")
        return
    # 계정 생성
    result = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"role": "admin"}
    })
    print("Supabase에 총관리자 계정이 생성되었습니다:", result)

# 관리자 계정 생성 후 호출
create_supabase_admin()

@app.route('/dashboard')
@login_required
def dashboard():
    # 대시보드 내용
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('로그아웃 되었습니다.')
    return redirect('/login')

if __name__ == '__main__':
    logger.info('레스토랑 시스템 시작')
    app.run(host='0.0.0.0', port=8080, debug=True)


