from models import User, Contract
from datetime import datetime, timedelta
from utils.salary_calculator import calculate_salary
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_kakao_message(phone: str, message: str):
    """카카오톡 메시지 전송"""
    # 실제 카카오톡 API 연동 시 사용
    # 현재는 로그만 출력
    print(f"[카카오톡 발송] {phone} → {message}")

def send_sms(phone: str, message: str):
    """SMS 메시지 전송"""
    # 실제 SMS API 연동 시 사용
    # 현재는 로그만 출력
    print(f"[SMS 발송] {phone} → {message}")

def send_salary_notification(user_id: int, salary_info: dict):
    """급여 지급 알림 전송"""
    try:
        user = User.query.get(user_id)
        if not user or not user.phone:
            return False
            
        message = f"""[{user.name}님의 {salary_info['start_date']} ~ {salary_info['end_date']} 급여 내역]
총 급여: {salary_info['salary_breakdown']['total_salary']:,}원
- 기본급: {salary_info['salary_breakdown']['base_salary']:,}원
- 연장수당: {salary_info['salary_breakdown']['overtime_pay']:,}원
- 야간수당: {salary_info['salary_breakdown']['night_pay']:,}원
- 휴일수당: {salary_info['salary_breakdown']['holiday_pay']:,}원

공제 내역:
- 4대보험: {salary_info['insurance_premiums']['total_insurance']:,}원
- 소득세: {salary_info['tax_info']['tax_amount']:,}원

실수령액: {salary_info['net_salary']:,}원"""
        
        # 카카오톡과 SMS 모두 전송
        send_kakao_message(user.phone, message)
        send_sms(user.phone, message)
        
        return True
        
    except Exception as e:
        print(f"급여 알림 전송 중 오류 발생: {str(e)}")
        return False

def check_and_send_salary_notifications():
    """급여 지급일 전 알림 전송"""
    try:
        # 오늘 날짜
        today = datetime.now().date()
        
        # 유효한 계약 조회
        contracts = Contract.query.filter(
            Contract.end_date >= today,
            Contract.start_date <= today
        ).all()
        
        for contract in contracts:
            # 급여 지급일이 설정되어 있는 경우에만 처리
            if contract.pay_day:
                # 급여 지급일 확인
                payday = today.replace(day=contract.pay_day)
                
                # 급여 지급일이 7일 이내인 경우
                if 0 <= (payday - today).days <= 7:
                    # 이번 달 급여 계산
                    start_date = today.replace(day=1)
                    if today.month == 12:
                        end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
                    
                    # 급여 계산
                    salary_info = calculate_salary(contract.employee.user.id, start_date, end_date)
                    
                    # 알림 전송
                    send_salary_notification(contract.employee.user.id, salary_info)
                
    except Exception as e:
        print(f"급여 알림 확인 중 오류 발생: {str(e)}") 