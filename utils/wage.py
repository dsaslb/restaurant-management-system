from datetime import datetime, timedelta
from models import Attendance, Contract

def calculate_work_hours(employee_id, start_date, end_date):
    """특정 기간 동안의 총 근무 시간을 계산하는 함수
    
    Args:
        employee_id (int): 직원 ID
        start_date (date): 시작 날짜
        end_date (date): 종료 날짜
        
    Returns:
        float: 총 근무 시간 (시간 단위)
    """
    total_minutes = 0
    attendances = Attendance.query.filter(
        Attendance.employee_id == employee_id,
        Attendance.work_date >= start_date,
        Attendance.work_date <= end_date,
        Attendance.clock_in != None,
        Attendance.clock_out != None
    ).all()

    for a in attendances:
        diff = a.clock_out - a.clock_in
        total_minutes += diff.total_seconds() / 60

    return round(total_minutes / 60, 2)  # 시간 단위로 반환

def calculate_wage(contract, work_hours):
    """계약 조건에 따른 급여를 계산하는 함수
    
    Args:
        contract (Contract): 계약서 객체
        work_hours (float): 총 근무 시간
        
    Returns:
        float: 계산된 급여
    """
    if contract.pay_type == '시급제':
        return contract.wage * work_hours
    elif contract.pay_type == '주급제':
        return contract.wage * (work_hours / 40)  # 주 40시간 기준
    elif contract.pay_type == '월급제':
        return contract.wage
    else:
        return 0

def calculate_monthly_wage(employee_id, year, month):
    """월별 급여를 계산하는 함수
    
    Args:
        employee_id (int): 직원 ID
        year (int): 연도
        month (int): 월
        
    Returns:
        dict: 급여 계산 결과
    """
    # 해당 월의 시작일과 종료일 계산
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # 근무 시간 계산
    work_hours = calculate_work_hours(employee_id, start_date, end_date)
    
    # 현재 유효한 계약서 조회
    contract = Contract.query.filter(
        Contract.employee_id == employee_id,
        Contract.start_date <= end_date,
        Contract.end_date >= start_date,
        Contract.signed == True
    ).first()
    
    if not contract:
        return {
            'error': '유효한 계약서가 없습니다.',
            'work_hours': work_hours,
            'wage': 0
        }
    
    # 급여 계산
    wage = calculate_wage(contract, work_hours)
    
    return {
        'work_hours': work_hours,
        'wage': wage,
        'pay_type': contract.pay_type,
        'base_wage': contract.wage
    } 