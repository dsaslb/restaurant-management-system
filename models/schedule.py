from datetime import datetime
from extensions import db

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('schedules', lazy=True))

    def __repr__(self):
        return f'<Schedule {self.id}: {self.user.name} {self.date}>'

class ScheduleHistory(db.Model):
    __tablename__ = 'schedule_history'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # created, updated, deleted
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    schedule = db.relationship('Schedule')
    user = db.relationship('User')

    def __repr__(self):
        return f'<ScheduleHistory {self.id}: {self.action} {self.schedule_id}>' 