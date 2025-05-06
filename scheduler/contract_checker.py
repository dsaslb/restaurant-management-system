from datetime import datetime, timedelta
from models import Contract, Employee, User, db, Notification
from utils.alerts import send_admin_alert, send_kakao_alert
import logging

logger = logging.getLogger(__name__)

def check_contract_expiration():
    """계약 만료 체크 및 알림"""
    try:
        today = datetime.now().date()
        
        # 7일 후 만료되는 계약 조회
        upcoming_expiry = Contract.query.filter(
            Contract.end_date == today + timedelta(days=7),
            Contract.signed == True
        ).all()
        
        # 오늘 만료되는 계약 조회
        expiring_today = Contract.query.filter(
            Contract.end_date == today,
            Contract.signed == True
        ).all()
        
        # 만료된 계약 조회 (7일 이내)
        expired_contracts = Contract.query.filter(
            Contract.end_date < today,
            Contract.end_date >= today - timedelta(days=7),
            Contract.signed == True
        ).all()
        
        # 알림 전송
        for contract in upcoming_expiry:
            employee = Employee.query.get(contract.employee_id)
            if employee and employee.user:
                # 관리자에게 알림
                send_admin_alert(
                    f"[계약 만료 예정] {employee.user.name}님의 계약이 7일 후 만료됩니다.\n"
                    f"계약 기간: {contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}"
                )
                
                # 직원에게 카카오톡 알림
                if employee.user.phone:
                    try:
                        send_kakao_alert(
                            employee.user.phone,
                            f"[계약 만료 예정] 귀하의 계약이 7일 후 만료됩니다.\n"
                            f"계약 기간: {contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}\n"
                            f"갱신이 필요합니다."
                        )
                    except Exception as e:
                        logger.error(f"카카오톡 알림 전송 실패: {str(e)}")
        
        for contract in expiring_today:
            employee = Employee.query.get(contract.employee_id)
            if employee and employee.user:
                # 관리자에게 알림
                send_admin_alert(
                    f"[계약 만료] {employee.user.name}님의 계약이 오늘 만료됩니다.\n"
                    f"계약 기간: {contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}"
                )
                
                # 직원에게 카카오톡 알림
                if employee.user.phone:
                    try:
                        send_kakao_alert(
                            employee.user.phone,
                            f"[계약 만료] 귀하의 계약이 오늘 만료됩니다.\n"
                            f"계약 기간: {contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}\n"
                            f"갱신이 필요합니다."
                        )
                    except Exception as e:
                        logger.error(f"카카오톡 알림 전송 실패: {str(e)}")
        
        for contract in expired_contracts:
            employee = Employee.query.get(contract.employee_id)
            if employee and employee.user:
                # 관리자에게 알림
                send_admin_alert(
                    f"[계약 만료] {employee.user.name}님의 계약이 만료되었습니다.\n"
                    f"계약 기간: {contract.start_date.strftime('%Y-%m-%d')} ~ {contract.end_date.strftime('%Y-%m-%d')}"
                )
        
        logger.info(f"계약 만료 체크 완료: {len(upcoming_expiry)}건 만료 예정, {len(expiring_today)}건 오늘 만료, {len(expired_contracts)}건 만료됨")
        
    except Exception as e:
        logger.error(f"계약 만료 체크 중 오류 발생: {str(e)}")
        raise 

def notify_contract_renewal():
    """계약 만료 알림 전송"""
    try:
        today = datetime.now().date()
        contracts = Contract.query.filter(
            Contract.end_date == today + timedelta(days=7)
        ).all()
        
        for contract in contracts:
            employee = Employee.query.get(contract.employee_id)
            if employee:
                # 관리자에게 알림
                admin_notification = Notification(
                    recipient_id=employee.store.admin_id,
                    title="계약 만료 알림",
                    content=f"{employee.user.name}님의 계약이 7일 후 만료됩니다. 갱신을 진행해 주세요.",
                    notification_type="contract"
                )
                
                # 직원에게 알림
                employee_notification = Notification(
                    recipient_id=employee.user_id,
                    title="계약 만료 알림",
                    content="귀하의 계약이 7일 후 만료됩니다. 갱신 절차를 진행해 주세요.",
                    notification_type="contract"
                )
                
                db.session.add(admin_notification)
                db.session.add(employee_notification)
                
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"계약 만료 알림 전송 중 오류 발생: {str(e)}")
        return False 