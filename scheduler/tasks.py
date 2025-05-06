from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from models import Contract, db
from utils.alerts import send_admin_alert, send_alert
from models import Schedule, User, Employee
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def check_contract_expiry():
    """계약 만료일 자동 알림"""
    with db.app.app_context():
        today = datetime.now().date()
        upcoming_contracts = Contract.query.filter(
            Contract.end_date <= today + timedelta(days=30)
        ).all()

        for contract in upcoming_contracts:
            days_left = (contract.end_date - today).days
            if days_left <= 30:
                send_admin_alert(
                    f"[알림] 계약 만료 예정: {contract.employee.name}님의 계약이 {days_left}일 후 만료됩니다.",
                    notification_type='contract'
                )

    soon = datetime.utcnow().date() + timedelta(days=30)
    contracts = Contract.query.filter(Contract.end_date == soon).all()
    for c in contracts:
        send_alert(f"계약 만료 예정: {c.user_id} / 종료일: {c.end_date}")

def start_scheduler(app):
    """스케줄러 시작"""
    scheduler = BackgroundScheduler()
    
    # 매일 오전 9시에 계약 만료 확인
    scheduler.add_job(
        check_contract_expiry,
        trigger=CronTrigger(hour=9, minute=0),
        id='check_contract_expiry',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler 

from models import Schedule
from datetime import datetime, timedelta
from utils.alerts import send_admin_alert

def check_unconfirmed_schedules():
    yesterday = datetime.utcnow() - timedelta(days=1)
    unconfirmed = Schedule.query.filter(
        Schedule.confirmed == False,
        Schedule.created_at <= yesterday
    ).all()

    for s in unconfirmed:
        send_admin_alert(f"[알림] {s.employee.name}님이 {s.date} 스케줄을 아직 확인하지 않았습니다.")

def alert_unconfirmed_schedules():
    """미확인 스케줄 알림 전송"""
    try:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        unconfirmed = Schedule.query.filter(
            Schedule.date == yesterday,
            Schedule.confirmed == False
        ).all()

        for schedule in unconfirmed:
            # 직원 정보 조회
            employee = Employee.query.filter_by(user_id=schedule.user_id).first()
            if not employee:
                continue

            # 알림 메시지 생성
            message = (
                f"[알림] {employee.user.name} 직원이 "
                f"{schedule.date.strftime('%Y-%m-%d')}의 "
                f"근무 스케줄({schedule.start_time.strftime('%H:%M')}~{schedule.end_time.strftime('%H:%M')})을 "
                "확인하지 않았습니다."
            )

            # 알림 전송
            send_alert(message)
            logger.info(f"미확인 스케줄 알림 전송: {message}")

    except Exception as e:
        logger.error(f"미확인 스케줄 알림 처리 중 오류 발생: {str(e)}")

def init_scheduler(app):
    """스케줄러 초기화"""
    try:
        # 매일 오전 9시에 실행
        scheduler.add_job(
            alert_unconfirmed_schedules,
            CronTrigger(hour=9, minute=0),
            id='alert_unconfirmed_schedules',
            replace_existing=True
        )

        # 스케줄러 시작
        scheduler.start()
        logger.info("스케줄러가 시작되었습니다.")

    except Exception as e:
        logger.error(f"스케줄러 초기화 중 오류 발생: {str(e)}")
        raise

def shutdown_scheduler():
    """스케줄러 종료"""
    try:
        scheduler.shutdown()
        logger.info("스케줄러가 종료되었습니다.")
    except Exception as e:
        logger.error(f"스케줄러 종료 중 오류 발생: {str(e)}")
        raise


