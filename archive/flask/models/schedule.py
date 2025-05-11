from datetime import datetime, time
from extensions import db

class Schedule(db.Model):
    """근무 일정 모델"""
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    break_time = db.Column(db.Integer)  # 휴게시간(분)
    status = db.Column(db.String(20), default='pending')  # pending, approved, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    work_type = db.Column(db.String(50), nullable=False)  # 정규, 특근, 휴가 등
    is_approved = db.Column(db.Boolean, default=False)  # 승인 여부를 저장하는 속성 추가

    # 관계 설정
    employee = db.relationship('Employee', back_populates='schedules')
    history = db.relationship('ScheduleHistory', back_populates='schedule', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Schedule {self.employee_id} - {self.date}>'

class ScheduleHistory(db.Model):
    """일정 이력 모델"""
    __tablename__ = 'schedule_history'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # created, updated, deleted
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계 설정
    schedule = db.relationship('Schedule', back_populates='history')
    user = db.relationship('User', back_populates='schedule_history')

    def __repr__(self):
        return f'<ScheduleHistory {self.id}: {self.action} {self.schedule_id}>' 