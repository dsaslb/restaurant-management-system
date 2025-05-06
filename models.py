from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, String
from cryptography.fernet import Fernet
import base64

db = SQLAlchemy()

class EncryptedString(TypeDecorator):
    """암호화된 문자열을 저장하는 커스텀 타입"""
    impl = String
    cache_ok = True

    def __init__(self, length=None, **kwargs):
        super().__init__(length, **kwargs)
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            os.environ['ENCRYPTION_KEY'] = key.decode()
        self.fernet = Fernet(key if isinstance(key, bytes) else key.encode())

    def process_bind_param(self, value, dialect):
        """데이터베이스에 저장하기 전에 암호화"""
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return None

    def process_result_value(self, value, dialect):
        """데이터베이스에서 읽어올 때 복호화"""
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return None

class User(UserMixin, db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    """직원 모델"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    position = db.Column(db.String(64), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    base_salary = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('employee', uselist=False))

class Schedule(db.Model):
    """근무 일정 모델"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_at = db.Column(db.DateTime)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='schedules')
    confirmer = db.relationship('User', foreign_keys=[confirmed_by])
    creator = db.relationship('User', foreign_keys=[created_by])

class ScheduleHistory(db.Model):
    """근무 일정 변경 이력 모델"""
    __tablename__ = 'schedule_history'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_start = db.Column(db.String(5), nullable=False)
    old_end = db.Column(db.String(5), nullable=False)
    new_start = db.Column(db.String(5), nullable=False)
    new_end = db.Column(db.String(5), nullable=False)
    reason = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedule = db.relationship('Schedule', backref='history')
    user = db.relationship('User', backref='schedule_changes')

class Contract(db.Model):
    """계약서 모델"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    pay_type = db.Column(db.String(20), nullable=False)  # 시급제, 주급제, 월급제
    wage = db.Column(db.Integer, nullable=False)
    pay_day = db.Column(db.Integer, nullable=True)  # 월급제의 경우 지급일
    signed = db.Column(db.Boolean, default=False)
    signed_at = db.Column(db.DateTime, nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 갱신 이력 필드 추가
    renewed_from_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=True)
    previous_contract = db.relationship('Contract', remote_side=[id], uselist=False)
    
    # 관계 설정
    employee = db.relationship('Employee', backref=db.backref('contracts', lazy=True))
    
    def __repr__(self):
        return f'<Contract {self.id}>'

    def is_expiring_soon(self, days=7):
        """계약 만료가 임박했는지 확인"""
        today = date.today()
        return today <= self.end_date <= today + timedelta(days=days)
    
    def is_expired(self):
        """계약이 만료되었는지 확인"""
        return date.today() > self.end_date

    def to_dict(self):
        """계약서 정보를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'pay_type': self.pay_type,
            'wage': self.wage,
            'pay_day': self.pay_day,
            'signed': self.signed,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Attendance(db.Model):
    """근태 기록 모델"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)  # 출근 날짜 (2025-05-05)
    clock_in = db.Column(db.DateTime)  # 출근 시각
    clock_out = db.Column(db.DateTime)  # 퇴근 시각
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship('Employee', backref=db.backref('attendance', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'work_date': self.work_date.isoformat(),
            'clock_in': self.clock_in.strftime('%Y-%m-%d %H:%M:%S') if self.clock_in else None,
            'clock_out': self.clock_out.strftime('%Y-%m-%d %H:%M:%S') if self.clock_out else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Store(db.Model):
    """매장 모델"""
    __tablename__ = 'stores'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    status = db.Column(db.String(20), default='open')  # open, closed, maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'opening_time': self.opening_time.strftime('%H:%M') if self.opening_time else None,
            'closing_time': self.closing_time.strftime('%H:%M') if self.closing_time else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WorkLog(db.Model):
    """작업 로그 모델"""
    __tablename__ = 'work_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    work_type = db.Column(db.String(50), nullable=False)  # cleaning, cooking, serving, etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship('Employee', backref=db.backref('work_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'content': self.content,
            'work_type': self.work_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AlertLog(db.Model):
    """알림 로그 모델"""
    __tablename__ = 'alert_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # schedule, attendance, contract, system
    content = db.Column(db.Text, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='unread')  # unread, read, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', backref=db.backref('alert_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'content': self.content,
            'recipient_id': self.recipient_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Salary(db.Model):
    """급여 모델"""
    __tablename__ = 'salaries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    calculation_date = db.Column(db.Date, nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    overtime_pay = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    total_salary = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship('Employee', backref=db.backref('salaries', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'calculation_date': self.calculation_date.isoformat(),
            'base_salary': self.base_salary,
            'overtime_pay': self.overtime_pay,
            'bonus': self.bonus,
            'deductions': self.deductions,
            'total_salary': self.total_salary,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContractRenewalLog(db.Model):
    """계약 갱신 로그 모델"""
    __tablename__ = 'contract_renewal_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    old_end_date = db.Column(db.Date, nullable=False)
    new_end_date = db.Column(db.Date, nullable=False)
    renewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    renewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    contract = db.relationship('Contract', backref=db.backref('renewal_logs', lazy=True))
    renewer = db.relationship('User', backref=db.backref('contract_renewals', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'old_end_date': self.old_end_date.isoformat(),
            'new_end_date': self.new_end_date.isoformat(),
            'renewed_at': self.renewed_at.isoformat() if self.renewed_at else None,
            'renewed_by': self.renewed_by
        }

class SignatureLog(db.Model):
    """계약서 서명 로그 모델"""
    __tablename__ = 'signature_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    signer_name = db.Column(db.String(50), nullable=False)  # 서명자 이름
    signed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # 서명 당시 IP
    user_agent = db.Column(db.String(255))  # 브라우저 정보
    
    contract = db.relationship('Contract', backref=db.backref('signature_logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'signer_name': self.signer_name,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class ContractTemplate(db.Model):
    """계약서 템플릿"""
    __tablename__ = 'contract_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    creator = db.relationship('User', backref=db.backref('contract_templates', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }

class Holiday(db.Model):
    """공휴일 모델"""
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Holiday {self.date} - {self.name}>'

    @classmethod
    def is_holiday(cls, date):
        """해당 날짜가 공휴일인지 확인"""
        return cls.query.filter_by(date=date).first() is not None

    @classmethod
    def get_holiday_name(cls, date):
        """해당 날짜의 공휴일 이름을 반환"""
        holiday = cls.query.filter_by(date=date).first()
        return holiday.name if holiday else None

class Notification(db.Model):
    """알림 모델"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # schedule, attendance, feedback, system
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'title': self.title,
            'content': self.content,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WorkEvaluation(db.Model):
    """근무 평가 모델"""
    __tablename__ = 'work_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)
    work_intensity = db.Column(db.Integer, nullable=False)  # 1-5점
    feedback = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=True)  # 익명 여부
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 관계 설정
    employee = db.relationship('Employee', backref=db.backref('evaluations', lazy=True))
    
    def __init__(self, employee_id, work_date, work_intensity, feedback=None, is_anonymous=True):
        self.employee_id = employee_id
        self.work_date = work_date
        self.work_intensity = work_intensity
        self.feedback = feedback
        self.is_anonymous = is_anonymous
    
    def to_dict(self, include_employee=False):
        """평가 정보를 딕셔너리로 변환
        
        Args:
            include_employee (bool): 직원 정보 포함 여부
        """
        data = {
            'id': self.id,
            'work_date': self.work_date.strftime('%Y-%m-%d'),
            'work_intensity': self.work_intensity,
            'feedback': self.feedback,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if include_employee and not self.is_anonymous:
            data['employee'] = {
                'id': self.employee.id,
                'name': self.employee.user.name,
                'position': self.employee.position
            }
            
        return data

class TerminationDocument(db.Model):
    """퇴직/해고/계약해지 문서 모델"""
    __tablename__ = 'termination_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    document_type = db.Column(db.String(20), nullable=False)  # resignation, dismissal, mutual_termination
    reason = db.Column(db.Text, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 서명 관련
    signed_by_employee = db.Column(db.Boolean, default=False)
    signed_by_admin = db.Column(db.Boolean, default=False)
    employee_signed_at = db.Column(db.DateTime)
    admin_signed_at = db.Column(db.DateTime)
    pdf_path = db.Column(db.String(255))
    
    # 관계 설정
    employee = db.relationship('Employee', backref=db.backref('termination_documents', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_terminations', lazy=True))
    
    def __repr__(self):
        return f'<TerminationDocument {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'document_type': self.document_type,
            'reason': self.reason,
            'effective_date': self.effective_date.isoformat(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'signed_by_employee': self.signed_by_employee,
            'signed_by_admin': self.signed_by_admin,
            'employee_signed_at': self.employee_signed_at.isoformat() if self.employee_signed_at else None,
            'admin_signed_at': self.admin_signed_at.isoformat() if self.admin_signed_at else None,
            'pdf_path': self.pdf_path
        }

class Ingredient(db.Model):
    """식자재 모델"""
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 식재료, 조미료, 기타 등
    unit = db.Column(db.String(20), nullable=False)  # 예: 개, kg, L 등
    min_stock = db.Column(db.Float, nullable=False)  # 최소 재고량 (경고용)
    max_stock = db.Column(db.Float, nullable=False)  # 최대 재고허용량 (과발주 경고 기준)
    current_stock = db.Column(db.Float, default=0)  # 현재 재고량
    cost_per_unit = db.Column(db.Float, nullable=False)  # 단위당 가격
    supplier = db.Column(db.String(100))  # 공급업체
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    transactions = db.relationship('StockTransaction', backref='ingredient', lazy=True)
    order_items = db.relationship('OrderItem', backref='ingredient', lazy=True)
    usage_alerts = db.relationship('StockUsageAlert', backref='ingredient', lazy=True)
    
    def __init__(self, name, unit, min_stock=0, max_stock=999999, current_stock=0):
        self.name = name
        self.unit = unit
        self.min_stock = min_stock
        self.max_stock = max_stock
        self.current_stock = current_stock
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'current_stock': self.current_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def check_stock_levels(self):
        """재고 수준을 확인하고 상태를 반환"""
        if self.current_stock <= self.min_stock:
            return 'low'
        elif self.current_stock >= self.max_stock:
            return 'high'
        return 'normal'
    
    def get_stock_status(self):
        """재고 상태 정보를 반환"""
        status = self.check_stock_levels()
        return {
            'status': status,
            'current': self.current_stock,
            'min': self.min_stock,
            'max': self.max_stock,
            'unit': self.unit
        }
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class OrderItem(db.Model):
    """발주 품목 모델"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, received, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    order = db.relationship('PurchaseOrder', backref='order_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'ingredient_id': self.ingredient_id,
            'quantity': self.quantity,
            'cost_per_unit': self.cost_per_unit,
            'total_cost': self.total_cost,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StockItem(db.Model):
    """재고 품목 모델"""
    __tablename__ = 'stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'quantity': self.quantity,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StockTransaction(db.Model):
    """재고 거래 내역 모델"""
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'in' or 'out'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    
    # 관계 설정
    ingredient = db.relationship('Ingredient', backref='transactions')
    created_by_user = db.relationship('User', foreign_keys=[created_by], backref='created_transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'quantity': self.quantity,
            'transaction_type': self.transaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'notes': self.notes
        }

class NotificationSetting(db.Model):
    """알림 설정"""
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g. 'low_stock'
    hour = db.Column(db.Integer, default=9, nullable=False)
    minute = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NotificationSetting {self.name}>'

class NotificationLog(db.Model):
    """알림 로그 모델"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False)  # low_stock, contract, schedule 등
    content = db.Column(db.Text, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='sent')  # sent, failed, read
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipient = db.relationship('User', backref=db.backref('notification_logs', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_type': self.notification_type,
            'content': self.content,
            'recipient_id': self.recipient_id,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StockUsageAlert(db.Model):
    """재고 사용 알림 설정"""
    __tablename__ = 'stock_usage_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    threshold = db.Column(db.Float, nullable=False)  # 알림 기준 수량
    is_active = db.Column(db.Boolean, default=True)  # 알림 활성화 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    ingredient = db.relationship('Ingredient', backref=db.backref('usage_alerts', lazy=True))
    
    def __repr__(self):
        return f'<StockUsageAlert {self.ingredient.name} {self.threshold}>'

class MenuItem(db.Model):
    """메뉴 항목 모델"""
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # 판매가
    description = db.Column(db.Text)  # 메뉴 설명
    is_active = db.Column(db.Boolean, default=True)  # 판매 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RecipeItem(db.Model):
    """레시피 아이템 (메뉴별 소모 재료)"""
    __tablename__ = 'recipe_items'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # 메뉴 1개당 소모량
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    menu = db.relationship('MenuItem', backref='recipe_items')
    ingredient = db.relationship('Ingredient', backref='recipe_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_id': self.menu_id,
            'ingredient_id': self.ingredient_id,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SalesRecord(db.Model):
    """판매 기록 모델"""
    __tablename__ = 'sales_records'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)  # 판매 관련 메모

    menu = db.relationship('MenuItem', backref='sales_records')
    creator = db.relationship('User', backref='sales_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_id': self.menu_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'sold_at': self.sold_at.isoformat() if self.sold_at else None,
            'created_by': self.created_by,
            'notes': self.notes
        }



