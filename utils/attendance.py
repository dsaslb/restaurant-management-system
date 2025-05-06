# utils/attendance.py

from models import Attendance

def get_last_attendance(user_id):
    return Attendance.query.filter_by(user_id=user_id).order_by(Attendance.timestamp.desc()).first()

# utils/attendance.py

from models import Attendance
from datetime import date
from sqlalchemy import desc

def get_last_attendance(user_id):
    today = date.today()
    record = Attendance.query.filter_by(user_id=user_id).order_by(desc(Attendance.timestamp)).first()
    if not record:
        return "기록 없음"
    return {
        "action": record.action,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }
