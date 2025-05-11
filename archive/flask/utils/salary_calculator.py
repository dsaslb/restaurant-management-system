from models import User, Attendance, Contract
from datetime import datetime, timedelta
from extensions import db

# 상수 정의
STANDARD_HOURS_PER_WEEK = 40
OVERTIME_RATE = 1.5  # 연장 근무 수당 비율
NIGHT_RATE = 1.3     # 야간 근무 수당 비율
HOLIDAY_RATE = 2.0   # 휴일 근무 수당 비율
TAX_RATE = 0.033     # 소득세율 (3.3%)

# 4대보험 요율 (2024년 기준)
NATIONAL_PENSION_RATE = 0.045  # 국민연금 4.5%
HEALTH_INSURANCE_RATE = 0.03495  # 건강보험 3.495%
LONG_TERM_CARE_RATE = 0.00652  # 장기요양 0.652%
EMPLOYMENT_INSURANCE_RATE = 0.008  # 고용보험 0.8%

# 최저보험료 기준
MIN_MONTHLY_SALARY = 2_000_000  # 최저 월급여액
MAX_MONTHLY_SALARY = 5_000_000  # 최고 월급여액

def calculate_overtime_pay(hours: float, wage: float) -> float:
    """연장 근무 수당 계산"""
    return hours * wage * OVERTIME_RATE

def calculate_night_pay(hours: float, wage: float) -> float:
    """야간 근무 수당 계산"""
    return hours * wage * NIGHT_RATE

def calculate_holiday_pay(hours: float, wage: float) -> float:
    """휴일 근무 수당 계산"""
    return hours * wage * HOLIDAY_RATE

def calculate_tax(salary: float) -> dict:
    """세금 계산"""
    tax = salary * TAX_RATE
    return {
        'tax_amount': round(tax, 2),
        'net_salary': round(salary - tax, 2)
    }

def is_night_shift(start_time: datetime, end_time: datetime) -> bool:
    """야간 근무 여부 확인 (22:00-06:00)"""
    night_start = start_time.replace(hour=22, minute=0, second=0)
    night_end = end_time.replace(hour=6, minute=0, second=0)
    return start_time >= night_start or end_time <= night_end

def is_holiday(date: datetime.date) -> bool:
    """휴일 여부 확인 (토요일, 일요일)"""
    return date.weekday() >= 5

def calculate_insurance_premiums(salary: float, is_regular: bool = True) -> dict:
    """
    4대보험료 계산
    
    Args:
        salary (float): 월 급여액
        is_regular (bool): 정규직 여부 (기본값: True)
        
    Returns:
        dict: 보험료 계산 결과
    """
    # 비정규직의 경우 고용보험만 적용
    if not is_regular:
        employment_insurance = salary * EMPLOYMENT_INSURANCE_RATE
        return {
            'national_pension': 0,
            'health_insurance': 0,
            'long_term_care': 0,
            'employment_insurance': round(employment_insurance, 2),
            'total_insurance': round(employment_insurance, 2)
        }
    
    # 월 급여액이 최저/최고 기준액을 벗어나는 경우 조정
    adjusted_salary = max(min(salary, MAX_MONTHLY_SALARY), MIN_MONTHLY_SALARY)
    
    # 각 보험료 계산
    national_pension = adjusted_salary * NATIONAL_PENSION_RATE
    health_insurance = adjusted_salary * HEALTH_INSURANCE_RATE
    long_term_care = health_insurance * LONG_TERM_CARE_RATE
    employment_insurance = adjusted_salary * EMPLOYMENT_INSURANCE_RATE
    
    total_insurance = national_pension + health_insurance + long_term_care + employment_insurance
    
    return {
        'national_pension': round(national_pension, 2),
        'health_insurance': round(health_insurance, 2),
        'long_term_care': round(long_term_care, 2),
        'employment_insurance': round(employment_insurance, 2),
        'total_insurance': round(total_insurance, 2)
    }

def calculate_salary(user_id: int, start_date: datetime.date, end_date: datetime.date) -> dict:
    """
    특정 기간 동안의 급여를 계산합니다.
    
    Args:
        user_id (int): 직원 ID
        start_date (datetime.date): 시작일
        end_date (datetime.date): 종료일
        
    Returns:
        dict: 급여 계산 결과
    """
    try:
        # 사용자와 계약 정보 조회
        user = User.query.get(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
            
        contract = Contract.query.filter_by(employee_id=user.employee.id).first()
        if not contract:
            raise ValueError("계약 정보를 찾을 수 없습니다.")
            
        # 근무 기록 조회
        attendances = Attendance.query.filter(
            Attendance.user_id == user_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        # 근무 시간 계산
        total_hours = 0
        overtime_hours = 0
        night_hours = 0
        holiday_hours = 0
        
        for attendance in attendances:
            if attendance.clock_in and attendance.clock_out:
                work_time = attendance.clock_out - attendance.clock_in
                hours = work_time.total_seconds() / 3600
                
                # 기본 근무 시간
                if hours <= 8:
                    total_hours += hours
                else:
                    total_hours += 8
                    overtime_hours += hours - 8
                
                # 야간 근무 확인
                if is_night_shift(attendance.clock_in, attendance.clock_out):
                    night_hours += hours
                
                # 휴일 근무 확인
                if is_holiday(attendance.date):
                    holiday_hours += hours
        
        # 기본 급여 계산
        if contract.pay_type == "시급":
            base_salary = total_hours * contract.wage
        elif contract.pay_type == "월급":
            base_salary = contract.wage
        elif contract.pay_type == "주급":
            weeks = (end_date - start_date).days / 7
            standard_hours = STANDARD_HOURS_PER_WEEK * weeks
            if total_hours >= standard_hours:
                base_salary = contract.wage
            else:
                base_salary = contract.wage * (total_hours / standard_hours)
        else:
            raise ValueError("잘못된 급여 유형입니다.")
        
        # 추가 수당 계산
        overtime_pay = calculate_overtime_pay(overtime_hours, contract.wage)
        night_pay = calculate_night_pay(night_hours, contract.wage)
        holiday_pay = calculate_holiday_pay(holiday_hours, contract.wage)
        
        # 총 급여 계산
        total_salary = base_salary + overtime_pay + night_pay + holiday_pay
        
        # 4대보험 계산
        is_regular = contract.contract_type == "정규직"
        insurance_premiums = calculate_insurance_premiums(total_salary, is_regular)
        
        # 세금 계산
        tax_info = calculate_tax(total_salary)
        
        # 실수령액 계산
        net_salary = total_salary - insurance_premiums['total_insurance'] - tax_info['tax_amount']
        
        return {
            'user_id': user_id,
            'user_name': user.name,
            'pay_type': contract.pay_type,
            'contract_type': contract.contract_type,
            'wage': contract.wage,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'work_hours': {
                'total': round(total_hours, 2),
                'overtime': round(overtime_hours, 2),
                'night': round(night_hours, 2),
                'holiday': round(holiday_hours, 2)
            },
            'salary_breakdown': {
                'base_salary': round(base_salary, 2),
                'overtime_pay': round(overtime_pay, 2),
                'night_pay': round(night_pay, 2),
                'holiday_pay': round(holiday_pay, 2),
                'total_salary': round(total_salary, 2)
            },
            'insurance_premiums': insurance_premiums,
            'tax_info': tax_info,
            'net_salary': round(net_salary, 2)
        }
        
    except Exception as e:
        raise ValueError(f"급여 계산 중 오류 발생: {str(e)}") 