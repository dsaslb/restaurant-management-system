from datetime import date, timedelta
from models import db, Contract, Employee
from utils.kakao import send_kakao_to_admin, send_kakao_to_employee

def notify_upcoming_paydays():
    """급여일 7일 전 알림을 보내는 함수"""
    today = date.today()
    contracts = Contract.query.all()

    for contract in contracts:
        if not contract.pay_day:
            continue

        # 이번 달 급여일
        payday = date(today.year, today.month, contract.pay_day)

        # 이번 달 급여일이 지났으면 다음 달로 계산
        if payday < today:
            if today.month == 12:
                payday = date(today.year + 1, 1, contract.pay_day)
            else:
                payday = date(today.year, today.month + 1, contract.pay_day)

        # 오늘이 급여일 7일 전인가?
        if (payday - today).days == 7:
            employee = Employee.query.get(contract.employee_id)
            if not employee:
                continue

            # 알림 내용 구성
            message = (
                f"[급여일 알림]\n"
                f"{employee.name}님의 급여일({contract.pay_day}일)이 7일 남았습니다.\n"
                f"급여 지급을 준비해 주세요."
            )

            # 관리자에게 알림
            send_kakao_to_admin(employee.store_id, message)

            # 직원에게 알림
            send_kakao_to_employee(employee.id, message) 