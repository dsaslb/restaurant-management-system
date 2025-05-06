from models import Attendance, WorkFeedback
from collections import defaultdict
from datetime import time

def group_hour(t):
    # 시간대 구간화 (4시간 단위)
    if time(6, 0) <= t < time(10, 0):
        return "06:00-10:00"
    elif time(10, 0) <= t < time(14, 0):
        return "10:00-14:00"
    elif time(14, 0) <= t < time(18, 0):
        return "14:00-18:00"
    elif time(18, 0) <= t < time(22, 0):
        return "18:00-22:00"
    else:
        return "기타"

def analyze_workload():
    from datetime import timedelta
    from flask import current_app

    with current_app.app_context():
        attendances = Attendance.query.all()
        feedbacks = WorkFeedback.query.all()

        data = defaultdict(list)

        for a in attendances:
            hour_group = group_hour(a.clock_in)
            data[hour_group].append({'user_id': a.user_id})

        result = []
        for hour_group, records in data.items():
            count = len(records)
            fb_scores = [f.rating for f in feedbacks if group_hour(f.submitted_at.time()) == hour_group]
            avg_score = round(sum(fb_scores) / len(fb_scores), 1) if fb_scores else None

            suggestion = "적절"
            if avg_score and avg_score <= 2.5:
                suggestion = "인원 추가 권장"
            elif avg_score and avg_score >= 4.5 and count > 3:
                suggestion = "인원 감축 가능"

            result.append({
                '시간대': hour_group,
                '근무 인원': count,
                '평균 평점': avg_score,
                '의견': suggestion
            })
        return result
