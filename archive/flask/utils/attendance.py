# utils/attendance.py

from models import Attendance
from datetime import date
from sqlalchemy import desc
from typing import Union, Dict, Any

def get_last_attendance(user_id: int) -> Union[Dict[str, Any], str]:
    """사용자의 마지막 출석 기록을 조회합니다."""
    today = date.today()
    record = Attendance.query.filter_by(user_id=user_id).order_by(desc(Attendance.timestamp)).first()
    if not record:
        return "기록 없음"
    return {
        "action": record.action,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }
