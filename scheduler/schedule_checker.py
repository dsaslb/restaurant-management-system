from models import db, Schedule, User
from datetime import datetime, timedelta
from utils.alerts import send_admin_alert
import logging

logger = logging.getLogger(__name__)

def check_unconfirmed_schedules():
    """미확인 스케줄 체크 및 관리자 알림"""
    try:
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        
        # 미확인 스케줄 조회
        unconfirmed = Schedule.query.filter(
            Schedule.confirmed == False,
            Schedule.date <= one_day_ago
        ).all()
        
        if not unconfirmed:
            logger.info("미확인 스케줄이 없습니다.")
            return
            
        # 관리자 목록 조회
        admins = User.query.filter_by(is_admin=True).all()
        
        for schedule in unconfirmed:
            employee = User.query.get(schedule.user_id)
            if not employee:
                continue
                
            # 관리자에게 알림 전송
            message = (
                f"[스케줄 미확인 알림]\n"
                f"직원: {employee.name}\n"
                f"날짜: {schedule.date.strftime('%Y-%m-%d')}\n"
                f"시간: {schedule.start_time.strftime('%H:%M')} ~ {schedule.end_time.strftime('%H:%M')}\n"
                f"미확인 기간: 1일 이상"
            )
            
            for admin in admins:
                send_admin_alert(message)
                logger.info(f"미확인 스케줄 알림 전송: admin_id={admin.id}, schedule_id={schedule.id}")
                
    except Exception as e:
        logger.error(f"미확인 스케줄 체크 중 오류 발생: {str(e)}") 