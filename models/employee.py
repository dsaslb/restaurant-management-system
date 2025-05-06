from datetime import datetime
from extensions import db

class Employee(db.Model):
    """직원 모델"""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    hire_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', back_populates='employee')
    contracts = db.relationship('Contract', back_populates='employee', cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', back_populates='employee', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', back_populates='employee', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Employee {self.name}>'

class Contract(db.Model):
    """계약 모델"""
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    hourly_wage = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employee = db.relationship('Employee', back_populates='contracts')
    
    def __repr__(self):
        return f'<Contract {self.employee_id}>'

class Attendance(db.Model):
    """근태 모델"""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employee = db.relationship('Employee', back_populates='attendances')
    
    def __repr__(self):
        return f'<Attendance {self.employee_id} {self.date}>' 