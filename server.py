import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, make_response, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import requests
from sqlalchemy import func
from collections import defaultdict
from geopy.geocoders import Nominatim
import logging
from functools import wraps, lru_cache
from models import db, User, Attendance, Schedule, WorkLog, WorkFeedback, Employee, Contract
from alert_service import check_alerts
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from typing import Dict, List, Optional
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
import time
import psutil
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
from prometheus_flask_exporter import PrometheusMetrics
import threading
import queue
import json
import redis
from utils.attendance import get_last_attendance
from werkzeug.security import check_password_hash
from utils.pdf import generate_contract_pdf
from utils.alerts import send_admin_alert
from routes.schedule import schedule_bp

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('server.log', maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(schedule_bp)

# 환경 변수 로드
load_dotenv()

# 공통 예외 처리 미들웨어
class APIError(Exception):
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        return rv

@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    logger.error(f"API Error: {error.message} (Status: {error.status_code})")
    return response

@app.errorhandler(404)
def handle_not_found_error(error):
    logger.error(f"Not Found: {request.path}")
    return jsonify({
        'status': 'error',
        'message': '요청한 리소스를 찾을 수 없습니다.'
    }), 404

@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': '서버 내부 오류가 발생했습니다.'
    }), 500

# Health Check API
@app.route('/healthz')
def health_check():
    try:
        # DB 연결 확인
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# 공통 응답 포맷
def api_response(data=None, message='success', status_code=200):
    response = {
        'status': 'success',
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

# DB 세션 관리 데코레이터
def db_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise APIError('데이터베이스 오류가 발생했습니다.', 500)
    return decorated_function

# 입력 검증 데코레이터
def validate_input(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise APIError(f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Flask 애플리케이션 설정

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
db.init_app(app)

# 요청 제한 설정
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Prometheus 메트릭 설정
metrics = PrometheusMetrics(app)

# 커스텀 메트릭 정의
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
active_users = Gauge('active_users', 'Number of active users')
db_connections = Gauge('db_connections', 'Number of database connections')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')

# 성능 모니터링 큐
performance_queue = queue.Queue()

def monitor_performance():
    """시스템 성능 모니터링"""
    while True:
        try:
            with app.app_context():
                # 메모리 사용량
                memory = psutil.virtual_memory()
                memory_usage.set(memory.used)
                
                # CPU 사용량
                cpu = psutil.cpu_percent(interval=1)
                cpu_usage.set(cpu)
                
                # 데이터베이스 연결 수 (SQLite는 연결 풀을 사용하지 않음)
                db_connections.set(1)  # SQLite는 단일 연결만 사용
                
                # 성능 데이터 큐에 추가
                performance_data = {
                    'timestamp': datetime.now().isoformat(),
                    'memory_usage': memory.used,
                    'cpu_usage': cpu,
                    'db_connections': 1
                }
                performance_queue.put(performance_data)
            
            time.sleep(5)  # 5초마다 모니터링
        except Exception as e:
            logger.error(f"Performance monitoring error: {str(e)}")

# 모니터링 스레드 시작
def start_monitoring():
    monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
    monitor_thread.start()

@app.before_request
def before_request():
    """요청 전 처리"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """요청 후 처리"""
    # 요청 처리 시간 측정
    latency = time.time() - request.start_time
    request_latency.labels(request.method, request.path).observe(latency)
    
    # 요청 카운트 증가
    request_count.labels(request.method, request.path, response.status_code).inc()
    
    # 성능 데이터 로깅
    logger.info(f"Request: {request.method} {request.path} - {response.status_code} - {latency:.2f}s")
    
    return response

@app.route('/api/metrics')
def get_metrics():
    """성능 메트릭 조회"""
    try:
        # 큐에서 모든 성능 데이터 수집
        performance_data = []
        while not performance_queue.empty():
            performance_data.append(performance_queue.get())
        
        return jsonify({
            'status': 'success',
            'data': {
                'performance': performance_data,
                'active_users': active_users._value.get(),
                'db_connections': db_connections._value.get(),
                'memory_usage': memory_usage._value.get(),
                'cpu_usage': cpu_usage._value.get()
            }
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# JWT 설정
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(hours=1)

# 카카오 API 설정
KAKAO_API_KEY = 'dbde264d2824cc92205f707bfcbcc3bf'

# DB 생성
with app.app_context():
    db.drop_all()  # 기존 테이블 삭제
    db.create_all()  # 새 테이블 생성

def get_address_from_coords(lat, lon):
    try:
        geolocator = Nominatim(user_agent="restaurant_system")
        location = geolocator.reverse(f"{lat}, {lon}", language='ko')
        return location.address if location else "주소를 찾을 수 없습니다"
    except Exception as e:
        return f"주소 변환 오류: {str(e)}"

def get_stats():
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 오늘 출근 수
    today_in = Attendance.query.filter(
        Attendance.action == '출근',
        Attendance.timestamp >= today_start,
        Attendance.timestamp <= today_end
    ).count()
    
    # 오늘 퇴근 수
    today_out = Attendance.query.filter(
        Attendance.action == '퇴근',
        Attendance.timestamp >= today_start,
        Attendance.timestamp <= today_end
    ).count()
    
    # 현재 근무 중인 사람 수 (출근했지만 아직 퇴근하지 않은 사람)
    current_working = Attendance.query.filter(
        Attendance.action == '출근',
        ~Attendance.user_id.in_(
            db.session.query(Attendance.user_id).filter(
                Attendance.action == '퇴근',
                Attendance.timestamp >= today_start
            )
        )
    ).count()
    
    # 총 기록 수
    total_records = Attendance.query.count()
    
    return {
        'today_in': today_in,
        'today_out': today_out,
        'current_working': current_working,
        'total_records': total_records
    }

# 대시보드 페이지
@app.route('/')
def dashboard():
    # 필터 파라미터 가져오기
    store = request.args.get('store', '')
    name = request.args.get('name', '')
    date_filter = request.args.get('date', '')
    action = request.args.get('action', '')
    
    # 기본 쿼리
    query = Attendance.query
    
    # 필터 적용
    if store:
        query = query.filter(Attendance.store == store)
    if name:
        query = query.filter(Attendance.name.like(f'%{name}%'))
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
        next_day = filter_date.replace(day=filter_date.day + 1)
        query = query.filter(Attendance.timestamp >= filter_date, Attendance.timestamp < next_day)
    if action:
        query = query.filter(Attendance.action == action)
    
    # 정렬 및 결과 가져오기
    records = query.order_by(Attendance.timestamp.desc()).all()
    
    # 매장 목록 가져오기
    stores = [store[0] for store in db.session.query(Attendance.store).distinct().all()]
    
    # 통계 정보 가져오기
    stats = get_stats()
    
    # 결과 포맷팅
    formatted_records = [{
        'time': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'name': r.name,
        'store': r.store,
        'action': r.action,
        'address': r.address
    } for r in records]
    
    return render_template('dashboard.html', 
                         records=formatted_records,
                         stores=stores,
                         stats=stats)

# 출퇴근 기록 API
@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    try:
        data = request.json
        user = User.query.get(data['id'])
        
        if not user:
            return jsonify({'message': '사용자를 찾을 수 없습니다'}), 404
            
        address = get_address_from_coords(data['latitude'], data['longitude'])
        
        attendance = Attendance(
            user_id=user.id,
            action=data['action'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            address=address
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'message': '출퇴근 기록이 저장되었습니다',
            'address': address
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

# 모든 기록 보기 (API)
@app.route('/records', methods=['GET'])
def get_records():
    try:
        records = Attendance.query.order_by(Attendance.timestamp.desc()).all()
        return jsonify([{
            'id': r.user_id,
            'name': r.name,
            'store': r.store,
            'action': r.action,
            'time': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'location': f"{r.latitude}, {r.longitude}",
            'address': r.address
        } for r in records])
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 직원 등록 페이지
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# 직원 등록 처리
@app.route('/register_user', methods=['POST'])
def register_user():
    try:
        data = request.form
        
        # 필수 필드 검증
        required_fields = ['username', 'password', 'name', 'age', 'ssn', 'phone', 'store', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} 필드는 필수입니다.'
                }), 400
        
        # 사용자명 중복 검사
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'status': 'error',
                'message': '이미 사용 중인 사용자명입니다.'
            }), 400
        
        # 주민번호 중복 검사
        if User.query.filter_by(ssn=data['ssn']).first():
            return jsonify({
                'status': 'error',
                'message': '이미 등록된 주민번호입니다.'
            }), 400
        
        # 건강검진 날짜 변환
        health_check_date = None
        if data.get('health_check_date'):
            health_check_date = datetime.strptime(data['health_check_date'], '%Y-%m-%d').date()
        
        # 새 사용자 생성
        new_user = User(
            username=data['username'],
            password=data['password'],  # 실제로는 암호화 필요
            name=data['name'],
            age=int(data['age']),
            ssn=data['ssn'],
            address=data.get('address', ''),
            health_check_date=health_check_date,
            phone=data['phone'],
            store=data['store'],
            role=data['role'],
            salary_type=data.get('salary_type', '월급'),
            bank_account=data.get('bank_account', '')
        )
        
        # DB에 저장
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '직원 등록이 완료되었습니다.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 직원 목록 페이지
@app.route('/admin/employees')
def view_employees():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    employees = User.query.filter_by(role='employee').all()
    return render_template('employee_list.html', employees=employees)

# 직원 삭제
@app.route('/admin/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': '권한이 없습니다.'}), 403
        
    try:
        employee = User.query.get_or_404(employee_id)
        
        # 출퇴근 기록 삭제
        Attendance.query.filter_by(user_id=employee_id).delete()
        
        # 직원 삭제
        db.session.delete(employee)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '직원이 삭제되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 직원 수정 페이지
@app.route('/admin/employees/<int:employee_id>/edit', methods=['GET'])
def edit_employee_page(employee_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    employee = User.query.get_or_404(employee_id)
    return render_template('edit_employee.html', employee=employee)

# 직원 정보 수정
@app.route('/admin/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': '권한이 없습니다.'}), 403
        
    try:
        employee = User.query.get_or_404(employee_id)
        data = request.form
        
        # 필수 필드 검증
        required_fields = ['name', 'age', 'phone', 'store']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} 필드는 필수입니다.'
                }), 400
        
        # 정보 업데이트
        employee.name = data['name']
        employee.age = int(data['age'])
        employee.phone = data['phone']
        employee.store = data['store']
        employee.address = data.get('address', employee.address)
        employee.salary_type = data.get('salary_type', employee.salary_type)
        employee.bank_account = data.get('bank_account', employee.bank_account)
        
        if data.get('health_check_date'):
            employee.health_check_date = datetime.strptime(data['health_check_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '직원 정보가 수정되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 관리자 인증 미들웨어
@app.before_request
def require_login():
    protected_routes = ['/admin', '/admin/employees', '/admin/salary', '/admin/stats']
    if any(route in request.path for route in protected_routes):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            return render_template('login.html')

        # POST 요청일 때만 JSON 데이터 파싱
        data = request.get_json()
        username = data.get('username') if data else None
        password = data.get('password') if data else None
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return jsonify({'status': 'error', 'message': '사용자명과 비밀번호를 입력해주세요.'}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'status': 'error', 'message': '잘못된 사용자명 또는 비밀번호입니다.'}), 401

        token = create_jwt_token(user.id)
        return jsonify({
            'status': 'success',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })

    except Exception as e:
        logger.error(f"로그인 처리 중 오류 발생: {str(e)}")
        return jsonify({'status': 'error', 'message': '서버 오류가 발생했습니다.'}), 500

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# 급여 요약
@app.route('/admin/salary')
def salary_summary():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    employees = User.query.filter_by(role='employee').all()
    salary_table = []

    for emp in employees:
        records = Attendance.query.filter_by(user_id=emp.id, action='출근').all()
        count = len(records)

        if emp.salary_type == '시급':
            hourly_rate = 10000  # 예시
            total = count * 8 * hourly_rate
        elif emp.salary_type == '주급':
            total = 500000
        else:
            total = 2000000

        salary_table.append({
            'name': emp.name,
            'type': emp.salary_type,
            'count': count,
            'amount': total
        })

    return render_template('salary_summary.html', data=salary_table)

# 월별 통계
@app.route('/admin/stats')
def monthly_stats():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    all_records = Attendance.query.all()
    stats = defaultdict(int)

    for rec in all_records:
        key = rec.timestamp.strftime('%Y-%m')
        stats[key] += 1

    return render_template('monthly_stats.html', stats=stats)

# JWT 토큰 관련 함수 (중복 제거)
def create_jwt_token(user_id: int) -> str:
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[int]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# 토큰 검증 데코레이터 (중복 제거)
def token_required(f):
    """JWT 토큰 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'status': 'error', 'message': '토큰이 필요합니다.'}), 401
            
        token = token.replace('Bearer ', '')
        user_id = verify_jwt_token(token)
        if not user_id:
            return jsonify({'status': 'error', 'message': '유효하지 않은 토큰입니다.'}), 401
            
        return f(user_id, *args, **kwargs)
    return decorated

@app.route('/api/status/<int:user_id>')
@token_required
@limiter.limit("60 per minute")
def get_user_status(user_id: int):
    """사용자 상태 조회"""
    try:
        start_time = time.time()
        user = User.query.get_or_404(user_id)
        active_users.inc()  # 활성 사용자 수 증가
        
        # 응답 생성
        response = make_response(jsonify({
            'status': 'success',
            'data': {
                'user_id': user.id,
                'name': user.name,
                'role': user.role,
                'store_id': user.store,
                'last_attendance': get_last_attendance(user_id)
            }
        }))
        
        # 처리 시간 로깅
        latency = time.time() - start_time
        logger.info(f"User status request processed in {latency:.2f}s")
        
        return response
    except Exception as e:
        logger.error(f"Error getting user status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/attendance/<int:user_id>/clock-in', methods=['POST'])
@token_required
@limiter.limit("5 per minute")
def clock_in(user_id: int):
    """출근 처리"""
    try:
        today = date.today()
        existing = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.timestamp) == today
        ).first()
        
        if existing and existing.clock_in:
            return jsonify({'status': 'error', 'message': '이미 출근했습니다.'}), 400
            
        attendance = Attendance(
            user_id=user_id,
            timestamp=datetime.now(),
            clock_in=datetime.now().time()
        )
        db.session.add(attendance)
        db.session.commit()
        
        # 실시간 알림
        socketio.emit('attendance_update', {
            'user_id': user_id,
            'action': 'clock_in',
            'time': datetime.now().isoformat()
        })
        
        return jsonify({'status': 'success', 'message': '출근이 기록되었습니다.'})
    except Exception as e:
        logger.error(f"출근 처리 중 오류 발생: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/attendance/<int:user_id>/clock-out', methods=['POST'])
@token_required
@limiter.limit("5 per minute")
def clock_out(user_id: int):
    """퇴근 처리"""
    try:
        today = date.today()
        attendance = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.timestamp) == today
        ).first()
        
        if not attendance:
            return jsonify({'status': 'error', 'message': '출근 기록이 없습니다.'}), 400
            
        if attendance.clock_out:
            return jsonify({'status': 'error', 'message': '이미 퇴근했습니다.'}), 400
            
        attendance.clock_out = datetime.now().time()
        db.session.commit()
        
        # 실시간 알림
        socketio.emit('attendance_update', {
            'user_id': user_id,
            'action': 'clock_out',
            'time': datetime.now().isoformat()
        })
        
        return jsonify({'status': 'success', 'message': '퇴근이 기록되었습니다.'})
    except Exception as e:
        logger.error(f"퇴근 처리 중 오류 발생: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/worklog/<int:user_id>', methods=['GET', 'POST'])
@token_required
@limiter.limit("60 per minute")
def worklog(user_id: int):
    """근무 기록 관리"""
    try:
        if request.method == 'POST':
            content = request.json.get('content')
            if not content:
                return jsonify({'status': 'error', 'message': '근무 내용이 필요합니다.'}), 400
                
            worklog = WorkLog(
                user_id=user_id,
                content=content,
                date=date.today()
            )
            db.session.add(worklog)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': '근무 기록이 저장되었습니다.'})
            
        else:
            worklogs = WorkLog.query.filter_by(user_id=user_id).order_by(WorkLog.date.desc()).all()
            return jsonify({
                'status': 'success',
                'data': [{
                    'id': log.id,
                    'content': log.content,
                    'date': log.date.isoformat()
                } for log in worklogs]
            })
    except Exception as e:
        logger.error(f"근무 기록 처리 중 오류 발생: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/feedback/<int:user_id>', methods=['GET', 'POST'])
@token_required
@limiter.limit("60 per minute")
def feedback(user_id: int):
    """피드백 관리"""
    try:
        if request.method == 'POST':
            content = request.json.get('content')
            if not content:
                return jsonify({'status': 'error', 'message': '피드백 내용이 필요합니다.'}), 400
                
            feedback = WorkFeedback(
                user_id=user_id,
                content=content,
                date=date.today()
            )
            db.session.add(feedback)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': '피드백이 제출되었습니다.'})
            
        else:
            feedbacks = WorkFeedback.query.filter_by(user_id=user_id).order_by(WorkFeedback.date.desc()).all()
            return jsonify({
                'status': 'success',
                'data': [{
                    'id': fb.id,
                    'content': fb.content,
                    'date': fb.date.isoformat()
                } for fb in feedbacks]
            })
    except Exception as e:
        logger.error(f"피드백 처리 중 오류 발생: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/alerts/check')
def check_alerts_endpoint():
    """알림 체크"""
    try:
        alerts_sent = check_alerts()
        return jsonify({'message': f'{alerts_sent}개의 알림이 발송되었습니다.'}), 200
    except Exception as e:
        logger.error(f"알림 체크 중 오류 발생: {str(e)}")
        return jsonify({'message': '알림 체크에 실패했습니다.'}), 500

# 보호된 라우트 예시
@app.route('/api/protected')
@token_required
def protected_route(user_id):
    user = User.query.get(user_id)
    return jsonify({
        'status': 'success',
        'message': f'보호된 라우트에 접근했습니다. 사용자: {user.username}'
    })

@app.route('/contract/<int:contract_id>/pdf')
def generate_contract_pdf_route(contract_id):
    contract = Contract.query.get(contract_id)
    if not contract:
        return jsonify({'error': '해당 계약서를 찾을 수 없습니다.'}), 404

    output_path = f'static/pdfs/contract_{contract.id}.pdf'
    generate_contract_pdf(contract, output_path)
    return send_file(output_path)

if __name__ == '__main__':
    # Prometheus 메트릭 서버 시작
    prometheus_client.start_http_server(8000)
    
    # 모니터링 시작
    start_monitoring()
    
    # Flask 애플리케이션 시작
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 

# 직원 등록/조회
@app.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            data = request.form
            new_emp = Employee()
            name=data.get('name'),
            age=int(data.get('age')),
            rrn=data.get('rrn'),
            address=data.get('address'),
            health_cert_date=datetime.strptime(data.get('health_cert_date'), '%Y-%m-%d'),
            phone=data.get('phone'),
            store_id=session.get('store_id')  # 로그인 시 store_id 저장 가정
            
            db.session.add(new_emp)
            db.session.commit()
            flash('직원 등록 완료!')
        except Exception as e:
            print("직원 등록 오류:", e)
            flash('직원 등록 실패')

    employees = Employee.query.filter_by(store_id=session.get('store_id')).all()
    return render_template('employees.html', employees=employees)

# 계약서 생성 페이지
@app.route('/contracts/new', methods=['GET', 'POST'])
@db_session_required
def create_contract():
    if not session.get('admin_logged_in'):
        raise APIError('인증이 필요합니다.', 401)

    if request.method == 'POST':
        try:
            data = request.form
            required_fields = ['employee_id', 'title', 'content', 'start_date', 'end_date']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                raise APIError(f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}')

            contract = Contract(
                employee_id=data.get('employee_id'),
                title=data.get('title'),
                content=data.get('content'),
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d'),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d'),
                signed=False
            )
            db.session.add(contract)
            db.session.commit()

            # 계약서 PDF 저장
            output_path = f'static/pdfs/contract_{contract.id}.pdf'
            contract.pdf_path = output_path
            generate_contract_pdf(contract, output_path)
            db.session.commit()

            return api_response(
                data={'contract_id': contract.id},
                message='계약서가 등록되고 PDF가 저장되었습니다.'
            )
        except ValueError as e:
            raise APIError('날짜 형식이 올바르지 않습니다.')
        except Exception as e:
            logger.error(f"계약서 생성 중 오류: {str(e)}")
            raise APIError('계약서 생성 중 오류가 발생했습니다.', 500)

    employees = Employee.query.filter_by(store_id=session.get('store_id')).all()
    return render_template('contract_form.html', employees=employees)

# 계약서 목록 조회
@app.route('/contracts')
@db_session_required
def list_contracts():
    if not session.get('admin_logged_in'):
        raise APIError('인증이 필요합니다.', 401)

    try:
        contracts = Contract.query.join(Employee).filter(
            Employee.store_id == session.get('store_id')
        ).all()
        return api_response(data=[{
            'id': c.id,
            'title': c.title,
            'employee_name': c.employee.name,
            'start_date': c.start_date.isoformat(),
            'end_date': c.end_date.isoformat(),
            'signed': c.signed
        } for c in contracts])
    except Exception as e:
        logger.error(f"계약서 목록 조회 중 오류: {str(e)}")
        raise APIError('계약서 목록을 불러오는 중 오류가 발생했습니다.', 500)

# 서명 기능
@app.route('/contracts/<int:contract_id>/sign', methods=['POST'])
@db_session_required
def sign_contract(contract_id):
    if not session.get('admin_logged_in'):
        raise APIError('인증이 필요합니다.', 401)

    try:
        contract = Contract.query.get_or_404(contract_id)
        contract.signed = True
        contract.signed_at = datetime.now()
        db.session.commit()
        return api_response(message='계약서에 서명이 완료되었습니다.')
    except Exception as e:
        logger.error(f"계약서 서명 중 오류: {str(e)}")
        raise APIError('계약서 서명 중 오류가 발생했습니다.', 500)

# 계약서 PDF 생성 및 다운로드
@app.route('/contract/<int:contract_id>/pdf')
@db_session_required
def generate_contract_pdf_route(contract_id):
    if not session.get('admin_logged_in'):
        raise APIError('인증이 필요합니다.', 401)

    try:
        contract = Contract.query.get_or_404(contract_id)
        output_path = f'static/pdfs/contract_{contract.id}.pdf'
        generate_contract_pdf(contract, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        logger.error(f"PDF 생성 중 오류: {str(e)}")
        raise APIError('PDF 생성 중 오류가 발생했습니다.', 500)

# 스케줄 저장 API
@app.route('/api/schedule', methods=['POST'])
def save_schedule():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'unauthorized'}), 401

    data = request.get_json()
    new_schedule = Schedule(
        employee_id=data['employee_id'],
        date=datetime.strptime(data['date'], '%Y-%m-%d'),
        start_time=datetime.strptime(data['start'], '%H:%M').time(),
        end_time=datetime.strptime(data['end'], '%H:%M').time()
    )
    db.session.add(new_schedule)
    db.session.commit()
    return jsonify({'status': 'success'})

# 계약 만료일 자동 알림
def check_contract_expiry():
    today = date.today()
    upcoming_contracts = Contract.query.filter(
        Contract.end_date <= today + timedelta(days=7),
        Contract.signed == True
    ).all()

    for c in upcoming_contracts:
        days_left = (c.end_date - today).days
        if days_left == 7 or days_left == 0:
            send_admin_alert(
                f"[알림] {c.employee.name}님의 계약이 {days_left}일 후 만료됩니다."
            )
#  스케줄 라우트
@app.route('/schedule')
def schedule_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('schedule.html')

# 스케줄 확인 API
@app.route('/api/schedule/confirm/<int:schedule_id>', methods=['POST'])
def confirm_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    schedule.confirmed = True
    db.session.commit()
    return jsonify({'status': 'confirmed'})

@app.route('/generate-contract/<int:contract_id>')
def generate_contract_pdf_route(contract_id):
    contract = Contract.query.get(contract_id)  # ✅ 여기서 contract를 정의해줘야 함

    if not contract:
        return jsonify({'error': '계약서 정보를 찾을 수 없습니다.'}), 404

    output_path = f'pdfs/contract_{contract.id}.pdf'
    generate_contract_pdf(contract, output_path)  # 이제 오류 안 남

    return send_file(output_path)



