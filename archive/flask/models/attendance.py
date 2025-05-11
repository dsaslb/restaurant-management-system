from extensions import db
from datetime import datetime

class Attendance(db.Model):
    """출근부 모델"""
    __tablename__ = 'attendance'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')  # present, absent, late, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    employee = db.relationship('Employee', back_populates='attendances')

    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>' 