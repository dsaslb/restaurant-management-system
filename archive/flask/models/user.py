from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # admin, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    employee = db.relationship('Employee', back_populates='user', uselist=False)
    orders = db.relationship('Order', back_populates='user', lazy=True)
    schedule_history = db.relationship('ScheduleHistory', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    evaluations = db.relationship('WorkEvaluation', back_populates='evaluator', lazy=True)
    
    @property
    def is_admin(self):
        """관리자 여부를 반환합니다."""
        return self.role == 'admin' if self.role else False
    
    def set_password(self, password):
        """비밀번호 설정"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>' 